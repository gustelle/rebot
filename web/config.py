# -*- coding: utf-8 -*-

# This file contains the configuration of the scrapy service

import os
import pwd
import logging
from distutils.util import strtobool

import ujson as json

LOGGER = logging.getLogger('app')


class ElasticsearchConfig(object):

    # the Elasticsearch hosts
    # default is localhost
    ES_HOST = os.getenv('ES_HOST', default='http://localhost:9200')

    # control the number of shards, uncontrolled size of sharding impacts performance
    # see https://www.elastic.co/fr/blog/how-many-shards-should-i-have-in-my-elasticsearch-cluster
    # using max() ensures default value is 1 if ES_SHARDS is set to ''
    ES_SHARDS = max([1, int('0' + os.getenv('ES_SHARDS', default='5'))])

    # default : no replica on the cluster
    ES_REPLICAS = int('0' + os.getenv('ES_REPLICAS', default='0'))

    # pagination in Elasticsearch
    # using max() ensures default value is 1000 if ES_PAGE_SIZE is set to ''
    # drawback: config lower than 100 will never be taken into account
    RESULTS_PER_PAGE = max([20, int('0' + os.getenv('ES_PAGE_SIZE', default='20'))])


class StandardConfig(object):

    LOG_LEVEL = logging.INFO

    # the URL to send the logging entries
    # if None is set, SENTRY will not be used
    SENTRY_URL = os.getenv('SENTRY_URL', default=None)

    # the TAG in Sentry to retrieve the logging entries
    # this is useful to separate environments in sentry
    SENTRY_TAG = os.getenv('SENTRY_TAG', default='dev')

    # the root node where to store the catalogs in firebase
    ROOT_NODE = 'real-estate'

    # the root node where to store the prediction models in firebase
    # MODELS_ROOT_NODE = 'prediction_models'

    # you must pass a string containing the JSON config of firebase
    # like this one :
    #   {
    #   "apiKey": "xxx",
    #   "authDomain": "xxx",
    #   "databaseURL": "xxx",
    #   "projectId": "xxx",
    #   "storageBucket": "xxx",
    #   "messagingSenderId": "xxx"
    # }
    # see the doc https://www.appypie.com/faqs/how-can-i-get-api-key-auth-domain-database-url-and-storage-bucket-from-my-firebase-account
    FIREBASE_CONFIG = json.loads(os.getenv('FIREBASE_CONFIG'))

    # you must pass your login and password as environment variables
    FIREBASE_AUTH = {
    	"login": os.getenv('FIREBASE_LOGIN', default=''),
    	"password": os.getenv('FIREBASE_PASSWORD', default=''),
    }

    # the number of open connections to firebase
    FIREBASE_POOL = 2

    # the life duration of the firebase token
    FIREBASE_TOKEN_TIMEOUT = 60*10 # in seconds

    # the default zone when no one is provided
    DEFAULT_ZONE = "mel"

    # when starting the app, some base data are installed
    # if a timestamp is present and fresher than  INSTALLATION_TIMESTAMP_TIMEOUT
    # nothing is instaled
    INSTALLATION_TIMESTAMP_TIMEOUT = 0  # in seconds, 0 means no timeout, never proceed to install at startup 
    INSTALL_BASE_DATA = bool(strtobool(os.getenv('INSTALL_BASE_DATA', default='0')))


class QueueConfig(object):
    REDIS_URL = os.getenv('REDIS_URL', default='redis://localhost:6379/0')


# default configuration is DEV
ES = ElasticsearchConfig
ENV = StandardConfig
Q = QueueConfig
