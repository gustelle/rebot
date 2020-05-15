import sys
import os, errno
import shutil
import fnmatch
import codecs
import random
import string
import time

import pytest

from elasticsearch import Elasticsearch, ElasticsearchException

import ujson as json

from main import app

from tests.data.products import VALID_PRODUCTS, INVALID_PRODUCTS
from tests.data.base_data import ZONE, CATALOG

import config

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
def dataset(monkeysession):
    """Provides dataset for each type of object (Product, Catalog)
    """
    ############################################################################
    # setup the data

    # elastic connection
    catalogs_test_index = ZONE
    host = os.getenv('ES_HOST')
    client = Elasticsearch(hosts=[host])
    try:
        client.indices.create(index=catalogs_test_index)
        print(f"Created Index '{catalogs_test_index}' in {host}")
    except ElasticsearchException as e:
        print(f"Index init for {catalogs_test_index} error: {e}")

    # insert products
    products_with_cat = VALID_PRODUCTS
    for _product in products_with_cat:
        _product['catalog'] = CATALOG

    products_ds = {'valid': products_with_cat, 'invalid': INVALID_PRODUCTS}
    for p_dict in products_ds['valid']:
        try:
            client = Elasticsearch(hosts=[os.getenv('ES_HOST')])
            client.index(
                    index=catalogs_test_index,
                    doc_type='_doc',
                    id=f"{p_dict['catalog']}_{p_dict['sku']}",
                    body = p_dict,
                    refresh=True
                )
        except ElasticsearchException as e:
            print(f"Error creating REP {p_dict}")

    # wait a bit for the refresh to be effective
    time.sleep(5)

    ############################################################################
    # the dataset itself

    def data():
        return {
            'products': products_ds
        }

    yield data()

    ############################################################################
    # tear down
    client.indices.delete(catalogs_test_index, ignore=[404])
