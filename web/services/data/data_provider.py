# -*- coding: utf-8 -*-

import logging

from elasticsearch_dsl import Search, Q

import six

from ..elastic_service import (ElasticSession, QueryBase, Product)

from ..cache import *
from objects import Catalog
import config
import utils


class _ObjectQuery():
    """
    proxy class for fetching Review, Product or Training objects

    :Example:
    >>> _ObjectQuery.find(catalog, Review, page=1)
    [Review<1>, Review<2>]

    """

    def get(self, zone, cls, id=None, **kwargs):
        """
        Generic method for getting a unit object

        :param cls: the type of object to be fetched
        """
        session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
        return session.get(cls, id=id, **kwargs)


    def _build_query(self, obj_type, zone=None, city=None, max_price=0, exclude=None, feature=None):
        logger = logging.getLogger('app')
        session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
        es_query = session.search(obj_type)

        #only 1 city among the list must match
        if bool(city) and utils.is_list(city):
            # transform the list of cities into a regexp
            # and add wildwards to enable searches like "Exclusivité sainghin xxx"
            rgxp = '|'.join([c for c in city if c.strip()!=''])
            es_query = es_query.query("regexp", city='.*('+rgxp+').*')
        else:
            logger.debug(f"ignored param city: {city}, must be a list")

        # all features in the list must match
        if bool(feature) and utils.is_list(feature):
            all_q = [Q("term", features=f) for f in feature]
            q = Q('bool', must=all_q)  # minimum_should_match=len(feature)
            es_query = es_query.query(q)
        else:
            logger.debug(f"ignored param feature: {feature}, must be a list")

        if max_price and max_price>0:
            try:
                es_query = es_query.filter('range', price={'gte': 0.0, 'lte': float(max_price)})
            except ValueError as ve:
                # do not filter, fallback
                logger.debug(f"ignore price param, failed to convert {max_price} to float")

        # exclude ids passed
        if bool(exclude) and utils.is_list(exclude):
            # prevent from querying blank ids which raises an error
            exclude = [item for item in exclude if item.strip()!='']
            q_exlude_ids = Q("ids", values=exclude)
            q = Q('bool', should=[Q('bool', must_not=[q_exlude_ids])])
            es_query = es_query.query(q)
        else:
            logger.debug(f"ignored param exclude: {exclude}, must be a list")

        return es_query


    def find(self, zone, obj_type, page=1, city=None, max_price=0, exclude=None, feature=None):
        """
        generic fetcher for objects

        :param page: for pagination purpose (default is 1)
        :param city: optional list of cities (default is None)
        :param max_price: optional max price to filter results (0 means no price limit)
        :param exclude: optional list of sku to exclude from the results (leave as None to include all SKU)
        :param feature: optional list of features. A feature is a "term" (a search facet) for Elasticsearch

        :Example:
        >>> ObjectQuery.find(Product)
        [Product<1>, Product<2>]

        """
        logger = logging.getLogger('app')

        es_query = self._build_query(
            obj_type,
            zone=zone,
            city=city,
            max_price=max_price,
            exclude=exclude,
            feature=feature
        )

        paginate_start = config.ES.RESULTS_PER_PAGE*(page-1)
        paginate_end = config.ES.RESULTS_PER_PAGE*(page)

        es_query = es_query[paginate_start:paginate_end]

        logger.debug(f"Find query: {es_query.to_dict()}")

        return es_query.execute()


    def count(self, zone, obj_type, city=None, max_price=0, exclude=None, feature=None):
        """
        generic object counter

        :Example:
        >>> ObjectQuery.count(catalog, Product)
        2
        """
        logger = logging.getLogger('app')

        es_query = self._build_query(
            obj_type,
            zone=zone,
            city=city,
            max_price=max_price,
            exclude=exclude,
            feature=feature
        )

        logger.debug(f"count query: {es_query.to_dict()}")
        logger.debug(f"count = {es_query.count()}")

        return es_query.count()


    def search(self, zone, obj_type):
        """returns an elasticsearch-py Search object pre-filtered on catalog"""

        session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
        return session.search(obj_type)


    def get_term_facets(self, zone, obj_type, term, startswith=None):
        """"""
        session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
        if not startswith:
            return session.get_term_facets(obj_type, term)
        else:
            logger = logging.getLogger('app')
            # see https://github.com/elastic/elasticsearch-dsl-py/issues/482
            # need to use the update_from_dict instead of from_dict
            s = session.search(obj_type).update_from_dict({
                "size": 0,
                "aggs" : {
                    "facets" : {
                      "terms": {
                          "field": term,
                          "size": 20,
                          "order" : { "_term" : "asc" },
                          "script": "if (_value.startsWith(\""+startswith+"\")) {return _value} else {return \"\"}"
                        }
                      }
                    }
                })
            logger.debug(f"query: {s.to_dict()}")
            results = s.execute()
            buckets = []
            for hit in results.aggregations.facets.buckets:
                buckets.append((hit['key'], hit['doc_count']))
            return buckets


class ProductService():
    """
    """

    def __init__(self, zone):
        """
        """
        self.zone = zone


    def get(self, id=None, **kwargs):
        """
        shortcut to ElasticSession.get(Product, id)
        """
        return _ObjectQuery().get(self.zone, Product, id=id, **kwargs)


    def find(self, page=1, city=None, max_price=0, exclude=None, feature=None):
        """
        returns a paged list of Product filtered on catalog

        :param city: optional list of cities
        :param max_price: optional max price to filter results
        """
        return _ObjectQuery().find(self.zone, Product, city=city, max_price=max_price, page=page, exclude=exclude, feature=feature)


    def count(self, city=None, max_price=0, exclude=None, feature=None):
        """
        counts all Products on catalog
        """
        return _ObjectQuery().count(self.zone, Product, city=city, max_price=max_price, exclude=exclude, feature=feature)


    def search(self):
        """
        provides a search instance on which you can scan the products
        """
        return _ObjectQuery().search(self.zone, Product)


    def get_term_facets(self, term, startswith=None):
        """
        fetches the facets of a given term in the catalog
        """
        return _ObjectQuery().get_term_facets(self.zone, Product, term, startswith=startswith)
