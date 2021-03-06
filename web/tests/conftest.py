import os #,errno
# import asyncio
# import sys
# import shutil
# import fnmatch
# import codecs
import random
# import string
import time

import pytest

import pyrebase
from elasticsearch import Elasticsearch, ElasticsearchException

import ujson as json

from main import app

from tests.data import (products, catalogs, users, areas)
from tests.data.base_data import ZONE

import config


FB_CI_ROOT = 'real-estate-ci'

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
            "area" : {"type" : "scaled_float", "scaling_factor": 100},
            "media" :  {"type" : "text", "index": "false"},
            "url" : {"type" : "text", "index": "false"},
            "quality_index": {"type" : "float"}, # computed, used for ranking & highlights
        }
    }
}

async def mock_coro(mock=None):
    return mock


@pytest.fixture
def test_cli(loop, sanic_client, mocker):
    # patch redis used to manage user session
    m = mocker.patch('aioredis.create_redis_pool')
    m.return_value=mock_coro()

    mocker.patch('_sanic_session.AIORedisSessionInterface')

    return loop.run_until_complete(sanic_client(app))


@pytest.fixture(scope="session")
def monkeysession(request):
    """
    monkeypatch is function scoped
    this is a fix for test_data fixture that I want session scoped
    see https://github.com/pytest-dev/pytest/issues/363
    """
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()



@pytest.fixture(scope='session')
def pyrebase_db(monkeysession):
    firebase = pyrebase.initialize_app(config.ENV.FIREBASE_CONFIG)
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(
        config.ENV.FIREBASE_AUTH.get('login'),
        config.ENV.FIREBASE_AUTH.get('password')
    )
    yield firebase.database()


@pytest.fixture(scope='session')
def elastic_client(monkeysession):
    host = os.getenv('ES_HOST')
    elastic_client = Elasticsearch(hosts=[host])
    yield elastic_client


@pytest.fixture(scope='session')
def firebase_root_node(monkeysession):
    yield FB_CI_ROOT


@pytest.fixture(scope='session')
def dataset(monkeysession):
    """Provides dataset for each type of object (Product, Catalog)
    """

    ############################################################################
    # setup the data

    """
    Products
    """
    catalogs_test_index = ZONE
    host = os.getenv('ES_HOST')
    elastic_client = Elasticsearch(hosts=[host])

    try:
        elastic_client.indices.create(
            index=catalogs_test_index,
            body={
                'settings': _SETTINGS,
                'mappings': _MAPPING
            })
    except ElasticsearchException as e:
        print(f"Index init for {catalogs_test_index} error: {e}")


    # insert products
    products_with_cat = products.VALID_PRODUCTS
    for _product in products_with_cat:
        _product['catalog'] = random.choice(catalogs.VALID_CATALOGS)['short_name']

    products_ds = {'valid': products_with_cat, 'invalid': products.INVALID_PRODUCTS}
    for p_dict in products_ds['valid']:
        try:
            # in the business logic, a product ID is made up of "cataog_sku"
            # let's try to stick to this logic
            # however we could use any logic for the ID, as long as it's reflected in the tests
            elastic_client.index(
                    index=catalogs_test_index,
                    doc_type='_doc',
                    id=f"{p_dict['catalog']}_{p_dict['sku']}",
                    body = p_dict,
                    refresh=True
                )
        except ElasticsearchException as e:
            print(f"Error creating REP {p_dict}")


    # firebase connection
    # patch the tenant node during the test sesion
    CATALOGS_ROOT_NODE = FB_CI_ROOT + '/catalogs'
    monkeysession.setattr('config.ENV.ROOT_NODE', FB_CI_ROOT)

    firebase = pyrebase.initialize_app(config.ENV.FIREBASE_CONFIG)
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(
        config.ENV.FIREBASE_AUTH.get('login'),
        config.ENV.FIREBASE_AUTH.get('password')
    )
    db = firebase.database()

    """
    Users
    """
    for c_dict in users.VALID_USERS:
        db.child(FB_CI_ROOT + '/users').child(c_dict['id']).set(c_dict)


    """
    Areas
    """
    for c_dict in areas.VALID_AREAS:
        db.child(FB_CI_ROOT + f"/areas/{ZONE}").child(c_dict['name']).set(c_dict)


    """
    Catalogs
    """
    for c_dict in catalogs.VALID_CATALOGS:
        c_dict['zone'] = ZONE
        c_dict['id'] = c_dict['short_name']
        db.child(CATALOGS_ROOT_NODE).child(c_dict['short_name']).set(c_dict)

    # wait a bit for the refresh to be effective
    time.sleep(5)


    ############################################################################
    # the dataset itself

    def data():
        return {
            'products': products_ds,
            'users': {
                'valid': users.VALID_USERS,
                'invalid': users.INVALID_USERS
            },
            'areas': {
                'valid': areas.VALID_AREAS,
                'invalid': areas.INVALID_AREAS
            },
            'catalogs': {
                'valid': catalogs.VALID_CATALOGS,
                'invalid': catalogs.INVALID_CATALOGS,
            }
        }

    yield data()

    ############################################################################
    # tear down

    elastic_client.indices.delete(catalogs_test_index, ignore=[404])
    db.child(FB_CI_ROOT).remove()
