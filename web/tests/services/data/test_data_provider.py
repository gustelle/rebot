# -*- coding: utf-8 -*-

import copy
import pytest
import random
import time

from pytest import raises

from unittest.mock import patch

from elasticsearch import Elasticsearch, ElasticsearchException
from elasticsearch_dsl import Search

from services.elastic_service import ElasticSession, Product
from services.data.data_meta import CatalogMeta
from services.data.data_provider import ProductService

from tests.data.base_data import ZONE
from tests.data.products import get_product_id

import config


@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestProductService(object):
    """
    The search method returns Review type objects
    """

    async def test_get_product(self, monkeypatch, mocker, dataset):
        """
        """
        service = CatalogMeta()
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
        catalog = service.get_the_catalog(catalog_dataset[0]['short_name'])

        data_provider = ProductService(catalog.zone)

        a_product = copy.deepcopy(dataset['products']['valid'][0])

        # reminder : a product ID is made up of catalog_sku
        # see in conftest.py
        p = data_provider.get(id=f"{a_product['catalog']}_{a_product['sku']}")

        assert isinstance(p, Product)
        assert p.meta.id == f"{p['catalog']}_{p['sku']}" == f"{a_product['catalog']}_{a_product['sku']}"


    async def test_find_sorting(self, monkeypatch, mocker, dataset, elastic_client):
        """
        products with "is_new"=True come first
        then products are sorted by quality index
        """
        products = copy.deepcopy(dataset['products']['valid'])

        random_product_1 = random.choice(products)
        random_product_1['is_new'] = True
        random_product_1['quality_index'] = 2

        random_product_2 = random.choice(products)
        random_product_2['is_new'] = True
        random_product_2['quality_index'] = 2.1

        # the first product is is_new = true
        # the others are is_new = false --> the 1st product should come first in the results
        for i, p in enumerate(products):
            if get_product_id(p)!=get_product_id(random_product_1)\
                and get_product_id(p)!=get_product_id(random_product_2):
                p['is_new'] = False
            elastic_client.index(
                    index=ZONE,
                    doc_type='_doc',
                    id=get_product_id(p),
                    body=p,
                    refresh=True
                )

        # wait for the refresh to be effective
        # short sleep times are unsafe
        time.sleep(5)

        service = CatalogMeta()
        catalog_dataset = dataset['catalogs']['valid']
        catalog = service.get_the_catalog(catalog_dataset[0]['short_name'])
        data_provider = ProductService(catalog.zone)

        ps, count = data_provider.find()

        # the 1st item of the results should be random_product_2, then random_product_1
        # then the others
        assert ps[0].meta.id == get_product_id(random_product_2)
        assert ps[1].meta.id == get_product_id(random_product_1)


    async def test_find_product_by_price_and_city(self, monkeypatch, mocker, dataset):
        """
        the products found must comply with the filtering params passed (max_price, city, exlude, feature)
        city can be a single string or an array of strings
        """
        service = CatalogMeta()
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
        catalog = service.get_the_catalog(catalog_dataset[0]['short_name'])

        data_provider = ProductService(catalog.zone)

        a_product = copy.deepcopy(dataset['products']['valid'][0])

        # print(f"a_product: {a_product}")

        ps, count = data_provider.find(city=[a_product['city']], max_price=a_product['price'])

        assert len(ps) > 0
        assert all([isinstance(p, Product) for p in ps])
        assert all([e.city == a_product['city'] for e in ps])
        assert all([e.price <= a_product['price'] for e in ps])


    async def test_find_product_with_exclusion_of_ids(self, monkeypatch, mocker, dataset):
        """
        exclude an id, verify it is not in the results
        """
        service = CatalogMeta()
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
        catalog = service.get_the_catalog(catalog_dataset[0]['short_name'])

        data_provider = ProductService(catalog.zone)

        a_product = copy.deepcopy(dataset['products']['valid'][0])
        id_to_exclude = a_product['sku']

        ps, count = data_provider.find(exclude=[id_to_exclude])

        assert all([id_to_exclude!=result.meta.id for result in ps])


    async def test_find_product_by_catalog(self, monkeypatch, mocker, dataset):
        """query by catalog only
        """
        service = CatalogMeta()
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
        catalog = service.get_the_catalog(catalog_dataset[0]['short_name'])

        data_provider = ProductService(catalog.zone)
        ps, count = data_provider.find(catalog=catalog.short_name)

        assert len(ps) > 0
        assert all([isinstance(p, Product) for p in ps])
        assert all([e.catalog == catalog.short_name for e in ps])


    async def test_find_product_by_catalog_city_max_price(self, monkeypatch, mocker, dataset):
        """combine different terms to query results"""

        service = CatalogMeta()
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
        catalog = service.get_the_catalog(catalog_dataset[0]['short_name'])
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        data_provider = ProductService(catalog.zone)
        ps, count = data_provider.find(catalog=catalog.short_name, city=[a_product['city']], max_price=a_product['price'])

        assert len(ps) > 0
        assert all([isinstance(p, Product) for p in ps])
        assert all([e.city == a_product['city'] for e in ps])
        assert all([e.price <= a_product['price'] for e in ps])
        assert all([e.catalog == catalog.short_name for e in ps])
