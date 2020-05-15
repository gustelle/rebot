# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import logging
import collections
from datetime import datetime

from elasticsearch import Elasticsearch, NotFoundError, ElasticsearchException
import elasticsearch.helpers as helpers

from elasticsearch_dsl import (Search, Index, Document, Date, Boolean, Byte, Integer,
    HalfFloat, Short, ScaledFloat, Float, Keyword, Text, MetaField,
    Nested, InnerDoc, Join, analysis)
from elasticsearch_dsl.faceted_search import FacetedSearch, TermsFacet

from elasticsearch_dsl.response import Hit
from elasticsearch_dsl.serializer import AttrJSONSerializer
from elasticsearch_dsl.exceptions import ValidationException

import utils
import config

from .exceptions import ServiceError, InitializationError

logger = logging.getLogger('app')


"""
Low level Elasticsearch access to objects
When using the objects Review and Product, you'll need to pass the 'index' and 'using' (client)
attributes, because they are not set at this object level for business logic reason
"""


class QueryBase(ABC):
    @abstractmethod
    def get(self, *args, **kwargs):
        pass


    @abstractmethod
    def find(self, *args, **kwargs):
        pass


    @abstractmethod
    def count(self, *args, **kwargs):
        pass


class ElasticSession(QueryBase):
    """
    Provides a wrapper around the business objects Product and Review
    to have variable index names according to the lang / industry at stake
    """
    def __init__(self, hosts=None, zone=None):
        """
        """
        if hosts is None or not utils.is_list(hosts):
            raise InitializationError("Bad parameter 'hosts'")

        self.logger = logging.getLogger('app')

        if not zone or zone.strip()=='':
            raise ValueError("Cannot init session without a zone")

        self.catalogs_index = zone

        self.es = Elasticsearch(hosts=hosts)
        self.logger.debug(f"Initiated Session on {hosts} for index '{self.catalogs_index}'")


    def get(self, cls, id=None, **kwargs):
        """
        convenience method to retrieve an object
        without having to pass index and using atts

        Returns None if not found
        """

        # NB: doc_types are deprecated in ES7.0, no way to insert it at the object level (through the Meta and Index class) it's not taken into account anymore
        # however, our current elasticsearch is a 6.x and requires a doc_type
        # passing the kwarg doc_type makes it compliant with both Elastic 7.x and Elastic 6.x
        return cls.get(
            index=self.get_catalogs_index(),
            using=self.get_client(),
            id=id,
            doc_type='_doc',
            ignore=404,
            **kwargs
        )


    def find(self, *args, **kwargs):
        raise NotImplementedError("prefer calling the search()")


    def count(self, *args, **kwargs):
        raise NotImplementedError("prefer counting from the search().count()")


    def get_client(self):
        return self.es


    def get_catalogs_index(self):
        """
        this is the name of the index where Product and Review objects
        are indexed
        """
        return self.catalogs_index


    def health(self):
        """
        checks the indices health with a timeout of 1 second
        """
        return self.es.cluster.health(level='indices', request_timeout=1)


    def search(self, cls):
        """
        convenience method to search for objects
        without having to pass index and using atts
        """

        _index = self.get_catalogs_index()
        return cls.search(
            index=_index,
            using=self.get_client()
        )


    def get_term_facets(self, cls, term):
        """
        wraps the dsl to provide easy access to a term facets
        """
        _index = self.get_catalogs_index()
        _client = self.get_client()

        class TermSearch(FacetedSearch):
            index = _index
            using = _client
            facets = {
                'term': TermsFacet(field=term),
            }

        # a hit is a tuple (term, count, selected)
        return list(map(
            lambda hit: (hit[0], hit[1]),
            TermSearch().execute().facets.term
        ))


class Serializable(Document):

    def to_json(self, include_meta=False):
        """Overrides the native document.to_dict()
        to overcome datetime serialization issues

        :param include_meta: if True, the meta attributes (index, routing, id) will be added to the dictionary

        :Example:
        >>> item.to_json(include_meta=True)
        {
            '_id': ...,
            '_routing': ...,
            '_index': ...,
            'title': ...,
            ...
        }
        """
        if include_meta:
            doc = self.to_flat_dict()
        else:
            doc = self.to_dict()

        # convert datetime for serialization
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()

        return doc


    def to_flat_dict(self):
        """flattens the dict hierarchy"""

        _all_fields = self.to_dict(include_meta=True)
        _source = _all_fields['_source']
        del _all_fields['_source']
        for key, value in _all_fields.items():
            _source[key] = value
        return _source


    @classmethod
    def from_dict(cls, dictionary):
        """
        load an object with a dictionary
        meta fields should be stored in the "meta" key, other fields are imported as-is

        :Example:
        >>> doc = {
                "_index": "test-index",
                "_id": "1",
                "_routing": "elasticsearch",
                "city": "Amsterdam",
            }
        >>> i = CatalogItem.from_dict(doc)
        >>> print(i.meta.id)
        1

        """
        _meta_info = {}
        # iterate over the meta keys which start with '_'
        for key, value in dictionary.items():
            if key.startswith('_'):
                # remove the _ and store the meta key the _meta_info dict
                _meta_info.update({key[1:]: value})

        # remove the _key from the dict
        # so that we can pass only data fields to the object
        for key in _meta_info.keys():
            del dictionary[f"_{key}"]

        # create the object with its data
        obj = cls.from_es({'_source': dictionary})

        # add the meta fields to the object
        for key, value in _meta_info.items():
            if 'meta' not in obj:
                obj['meta'] = {}
            obj.meta[key] = value
        return obj


class BaseItem(Serializable):

    # always put a timestamp on save
    def save(self, **kwargs):
        return super(BaseItem, self).save(**kwargs)


class CatalogItem(BaseItem):

    ######## Shared fields ############

    scraping_start_date = Date()
    scraping_end_date = Date()

    is_new = Boolean(index=True, required=False)

    catalog = Keyword(normalizer='folding_normalizer', index=True, required=True)

    def save(self, **kwargs):
        return super(CatalogItem, self).save(**kwargs)


class Product(CatalogItem):

    ######## Product fields ############

    sku = Text(required=True)

    title = Text(analyzer='folding_analyzer', norms=False, index=True, required=True)
    description = Text(analyzer='folding_analyzer', norms=False, index=True, required=False)
    city = Keyword(normalizer='folding_normalizer', index=True, required=True)
    # index the city both as text and keyword to search for cities
    # city_txt = Text(analyzer='folding_analyzer', norms=False, index=True, required=True, fields={'keyword': Keyword(normalizer='folding_normalizer', index=True)})

    features = Keyword(normalizer='folding_normalizer', index=True, multi=True)

    price = ScaledFloat(100, index=True, required=True)

    # this list of media URI (video, images, ...)
    media = Text(index=False, multi=True, required=True)
    url = Text(index=False, required=True)
