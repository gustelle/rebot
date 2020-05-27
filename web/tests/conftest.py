import os, errno
import sys
import shutil
import fnmatch
import codecs
import random
import string
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


@pytest.fixture
def test_cli(loop, sanic_client):
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
        elastic_client.indices.create(index=catalogs_test_index)
        print(f"Created Index '{catalogs_test_index}' in {host}")
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
