# -*- coding: utf-8 -*-
import logging
from numbers import Integral

from elasticsearch import Elasticsearch, ElasticsearchException, NotFoundError

import config


LOGGER = logging.getLogger('app')


# types will be removed in Elastic 7
# be careful if you use something different than _doc as doc_type
_DOCUMENT_TYPE = '_doc'

# index settings and mappings
_SETTINGS = {
    "analysis":{
        "normalizer": {
            # this normalizer enables to standardize the keywords
            # transforming all ascii sensitive chars into standard chars (ex: Bière --> biere)
            "folding_normalizer" : {
                "type"          : "custom",
                "filter"        : ["lowercase", "asciifolding"]
            }
        },
        "analyzer": {
            # analyze if for Text field what normalizer is for keyword fields
            # this enables to make a case insensitive search
            "folding_analyzer" : {
                "type"          : "custom",
                "tokenizer"     : "standard",
                "filter"        : ["lowercase", "asciifolding"],
                "char_filter":  [ "html_strip" ]
            }
        }
    },
    "number_of_shards": config.ES.ES_SHARDS,
    "number_of_replicas": config.ES.ES_REPLICAS
}

_MAPPING = {
    _DOCUMENT_TYPE: {
        "properties": {
            "scraping_start_date" : {"type" : "date"},
            "scraping_end_date" : {"type" : "date"},
            "is_new" : {"type" : "boolean"},
            "catalog" : {"type" : "keyword", "normalizer": "folding_normalizer"},
            "sku" : {"type" : "text"},
            "title" : {"type" : "text", "analyzer": "folding_analyzer", "norms": "false"},
            "description" : {"type" : "text", "analyzer": "folding_analyzer", "norms": "false"},
            "city" : {"type" : "keyword", "normalizer": "folding_normalizer"},
            "features" : {"type" : "keyword", "normalizer": "folding_normalizer"},
            "price" : {"type" : "scaled_float", "scaling_factor": 100},
            "media" :  {"type" : "text", "index": "false"},
            "url" : {"type" : "text", "index": "false"}
        }
    }
}


class MonitoringError(Exception):
    """To be raised at Monitoring time
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class IndexError(Exception):
    """To be raised at Index time
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class SearchError(Exception):
    """To be raised at Search time
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class ElasticSession():
    """Low level class to access Elasticsearch, given a zone and a list of hosts"""

    def __init__(self, hosts, zone):
        """raise ValueError"""

        if not zone or zone.strip()=='':
            raise ValueError("zone param must not be null or blank")

        self.hosts = hosts
        self.zone = zone


    def health(self):
        """health of the index"""
        try:
            client = Elasticsearch(hosts=self.hosts)
            return client.cluster.health(index=self.zone)
        except ElasticsearchException as ese:
            raise MonitoringError(ese)


    def get(self, id):
        """raise SearchError"""
        if not id or id.strip()=='':
            raise SearchError("Cannot get data without an id")

        try:
            client = Elasticsearch(hosts=self.hosts)
            res = client.get(
                    index=self.zone,
                    id=id,
                    doc_type=_DOCUMENT_TYPE
                )
            if res and res['found']:
                return res['_source']
            return None
        except NotFoundError as n:
            LOGGER.debug(f"Item {id} not found in index '{self.zone}'")
            return None
        except ElasticsearchException as err:
            raise SearchError(err)


    def delete_date_range(self, date_field, max_days):
        """
        deletes documents where the date_field is older than the given range,
        returns the number of docs deleted

        raises SearchError
        """
        if not date_field or date_field.strip()=='':
            raise SearchError("Cannot delete without a date_field")

        if not max_days or not isinstance(max_days, Integral):
            raise SearchError("Cannot delete without max_days")

        try:
            client = Elasticsearch(hosts=self.hosts)
            res = client.delete_by_query(
                        index=self.zone,
                        doc_type=_DOCUMENT_TYPE,
                        body={
                            "query": {
                                "range": {
                                    date_field: {
                                        "lte": f"now-{max_days}d"
                                    }
                                }
                            }
                        }
                    )

            return res['deleted']

        except ElasticsearchException as err:
            raise SearchError(err)


    def save(self, id, dict_of_data, force_refresh=False):
        """raise IndexError"""

        if not id or id.strip()=='':
            raise IndexError("Cannot index data without an id")

        try:
            client = Elasticsearch(hosts=self.hosts)
            response = client.index(
                    index=self.zone,
                    doc_type=_DOCUMENT_TYPE,
                    id=id,
                    body = dict_of_data,
                    refresh=force_refresh
                )
            LOGGER.info(f"Indexed document {id} in {self.zone}, refresh={force_refresh})")
        except ElasticsearchException as err:
            raise IndexError(err)


    def create_index(self):
        """raise IndexError"""
        try:
            client = Elasticsearch(hosts=self.hosts)
            index_exists = client.indices.exists(index=self.zone)

            # check if the Elasticsearch index exists
            if index_exists:
                raise IndexError(f"Index {self.zone} already existing")

            client.indices.create(
                index=self.zone,
                body={
                    'settings': _SETTINGS,
                    'mappings': _MAPPING
                }
            )

        except ElasticsearchException as err:
            LOGGER.critical(err)
            raise IndexError(err)


    def delete_index(self):
        """raise IndexError"""

        try:
            client = Elasticsearch(hosts=self.hosts)
            index_exists = client.indices.exists(index=self.zone)

            # check if the Elasticsearch index exists
            if index_exists == False:
                raise IndexError(f"Index {self.zone} does not exist")

            client.indices.delete(index=self.zone)

        except ElasticsearchException as err:
            raise IndexError(err)


class ElasticMonitoring():
    """static interface to monitor the Elasticsearch cluster, given a zone and a list of hosts"""

    @staticmethod
    def monitor(zone):
        """
        raise MonitoringError

        :Example:
        >>> ElasticMonitoring.monitor(zone)

        """
        try:
            session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
            return session.health()
        except ValueError as ve:
            raise MonitoringError(ve)


class ElasticCommand():
    """
    static interface to manage elasticsearch indices and data
    """

    @staticmethod
    def get(zone, id):
        """
        raise SearchError

        :Example:
        >>> ElasticCommand.get(zone, id)
        True

        """
        try:
            session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
            return session.get(id)
        except ValueError as ve:
            raise SearchError(ve)


    @staticmethod
    def save(zone, id, dict_of_data, force_refresh=False):
        """
        raise IndexError

        :Example:
        >>> ElasticCommand.save(zone, id, dict_of_data, force_refresh=False)
        True

        """
        try:
            session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
            return session.save(id, dict_of_data, force_refresh=force_refresh)
        except ValueError as ve:
            raise IndexError(ve)


    @staticmethod
    def delete_date_range(zone, date_field, max_days):
        """
        raise SearchError
        """
        try:
            session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
            return session.delete_date_range(date_field, max_days)
        except ValueError as ve:
            raise SearchError(ve)


    @staticmethod
    def create_index(zone):
        """
        raise IndexError

        :Example:
        >>> ElasticCommand.create_index(zone)
        True

        """
        try:
            session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
            return session.create_index()
        except ValueError as ve:
            raise IndexError(ve)


    @staticmethod
    def delete_index(zone):
        """
        raise IndexError

        :Example:
        >>> ElasticCommand.delete_index(zone)
        True

        """
        try:
            session = ElasticSession(hosts=[config.ES.ES_HOST], zone=zone)
            return session.delete_index()
        except ValueError as ve:
            raise IndexError(ve)
