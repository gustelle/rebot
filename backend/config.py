# -*- coding: utf-8 -*-

# This file contains the configuration of the scrapy service

import os
import pwd
import logging

import ujson as json

LOGGER = logging.getLogger('app')


class ElasticsearchConfig(object):

    # the Elasticsearch hosts
    # default is localhost
    ES_HOST =  os.getenv('ES_HOST', default='http://localhost:9200')

    # control the number of shards, uncontrolled size of sharding impacts performance
    # see https://www.elastic.co/fr/blog/how-many-shards-should-i-have-in-my-elasticsearch-cluster
    # using max() ensures default value is 1 if ES_SHARDS is set to ''
    ES_SHARDS = max([1, int('0' + os.getenv('ES_SHARDS', default='5'))])

    # default : no replica on the cluster
    ES_REPLICAS = int('0' + os.getenv('ES_REPLICAS', default='0'))


class StandardConfig(object):

    LOG_LEVEL = logging.INFO

    # the current Environment is used is sentry to filter messages
    ENVIRONMENT = os.getenv('ENVIRONMENT', default='dev')

    # force elasticsearch index  to be refreshed when updating data
    # and force features to be recalculated even if they have already been predicted and attached to the product
    # when set to True, the performance will be affected
    # use carefully
    FORCE_REFRESH = bool(max([0, int(os.getenv('FORCE_REFRESH', default=0))]))

    # sentry settings
    SENTRY_URL = os.getenv("SENTRY_URL")

    # the list of contexts where obsolete real estate ads will be deleted
    # it is required to define the index names
    CLEANUP_ZONES_LIST = ['mel']

    # the number of days after which obsolete real estate ads are deleted
    # from the index
    CLEANUP_REPS_AFTER_X_DAYS = 2


class QueueConfig(object):
    REDIS_URL = os.getenv('REDIS_URL', default='redis://localhost:6379/0')


# default configuration is DEV
ES = ElasticsearchConfig
ENV = StandardConfig
Q = QueueConfig
