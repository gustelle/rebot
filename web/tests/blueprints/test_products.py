# -*- coding: utf-8 -*-
import copy
import uuid
import random

from distutils.util import strtobool

import pytest

import ujson as json

from main import app

from services.exceptions import ServiceError
from services.data.data_meta import CatalogMeta
from services.data.data_provider import ProductService
from services.elastic_service import Product

from objects import User
import config

from tests.data.base_data import ZONE


async def test_get(test_cli, mocker, dataset):
    """verify the normal response"""
    training_dataset = copy.deepcopy(dataset['products']['valid'])

    data_provider = ProductService(ZONE)

    # product id
    id = f"{training_dataset[0]['catalog']}_{training_dataset[0]['sku']}"

    entry = data_provider.get(id=id)

    response = await test_cli.get(f"/products/{id}?zone={ZONE}")

    jay = await response.json()

    result = jay.get('result')

    assert result and result == entry.to_json(include_meta=True)



async def test_get_jsonschema_error(test_cli, mocker, dataset):
    """if the product is not compliant with the expected JSON schema, it is not returned"""

    # mock an invalid object returned by Elasticsearch
    training_dataset = copy.deepcopy(dataset['products']['valid'])

    # insert an _id which is required for schema validation
    for p in training_dataset:
        p['_id'] = f"{p['catalog']}_{p['sku']}"

    # delete the sku which will cause the json schema validation error
    a_product = training_dataset[0]
    sku = a_product['sku']
    del a_product['sku']

    mock_es = mocker.patch("services.data.data_provider.ProductService.get")
    mock_es.return_value = Product.from_dict(a_product)

    # product id
    id = f"{training_dataset[0]['catalog']}_{sku}"

    response = await test_cli.get(f"/products/{id}?zone={ZONE}")

    jay = await response.json()
    assert jay and not jay['success']


async def test_get_no_zone(test_cli, mocker, dataset):
    """zone param is required to fetch a product"""

    training_dataset = copy.deepcopy(dataset['products']['valid'])
    # product id
    id = f"{training_dataset[0]['catalog']}_{training_dataset[0]['sku']}"

    response = await test_cli.get(f"/products/{id}?zone=")

    assert response.status == 400


async def test_list_no_user(test_cli, mocker, dataset):
    """Invalid Usage"""

    response = await test_cli.get(f"/products?zone={ZONE}")

    assert response.status == 400


async def test_list_no_zone(test_cli, mocker, dataset):
    """Invalid Usage"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])

    response = await test_cli.get(f"/products?user_id={users_dataset[0]['id']}")

    assert response.status == 400


async def test_list(test_cli, mocker, dataset):
    """Use the API /products to list the products of a catalog"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    entries = data_provider.find(page=1)
    count = data_provider.count()

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}")

    jay = await response.json()

    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    response_prods = jay.get('products')

    assert all(_prod in list_entries for _prod in response_prods)
    assert jay.get('count') == count

    catalogs = dict()
    for catalog_item in dataset['catalogs']['valid']:
        catalogs[catalog_item['short_name']] = catalog_item

    assert jay.get('catalogs') == catalogs


async def test_list_products_jsonschema_error(test_cli, mocker, dataset):
    """in case a product is not compliant with the jsonschema, it is excluded from the returned list"""

    # mock an invalid object returned by Elasticsearch
    # for instance, no sku
    training_dataset = copy.deepcopy(dataset['products']['valid'])
    users_dataset = copy.deepcopy(dataset['users']['valid'])

    # insert an _id which is required for schema validation
    for p in training_dataset:
        p['_id'] = f"{p['catalog']}_{p['sku']}"

    a_product = training_dataset[0]
    del a_product['sku']

    mock_find = mocker.patch("services.data.data_provider.ProductService.find")
    mock_find.return_value = [Product.from_dict(p) for p in training_dataset]

    # training_dataset contains a product that should be deleted !

    mock_count = mocker.patch("services.data.data_provider.ProductService.count")
    mock_count.return_value = len(training_dataset)

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}")

    jay = await response.json()

    assert jay and jay['success']
    assert len(jay['products']) == len(training_dataset)-1
    assert jay['count'] == len(training_dataset)-1


async def test_list_filter_feature(test_cli, mocker, dataset):
    """The list is filtered with a feature"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    entries = data_provider.find(feature=["3 chambres"])
    count = data_provider.count(feature=["3 chambres"])

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}&feature=3 chambres")

    jay = await response.json()

    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    response_prods = jay.get('products')

    assert all("3 chambres" in _prod.features for _prod in list_entries)
    assert all(_prod in list_entries for _prod in response_prods)
    assert jay.get('count') == count


async def test_list_combine_features(test_cli, mocker, dataset):
    """The list is filtered with several features"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    features_list = ["3 chambres", "jardin"]

    entries = data_provider.find(feature=features_list)
    count = data_provider.count(feature=features_list)

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}&feature={','.join(features_list)}")

    jay = await response.json()

    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    response_prods = jay.get('products')

    assert all("3 chambres" in _prod.features for _prod in list_entries)
    assert all("jardin" in _prod.features for _prod in list_entries)
    assert all(_prod in list_entries for _prod in response_prods)
    assert jay.get('count') == count


async def test_list_exclude_deja_vu(test_cli, mocker, dataset):
    """Exclude deja_vu for a user"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    # take user[1] (id=2) which has some deja_vu
    # and make a manual exclusion of the deja_vu
    user_entries = data_provider.find(
        city=users_dataset[1]['filter']['city'],
        max_price=users_dataset[1]['filter']['max_price'],
        exclude=users_dataset[1]['deja_vu'][ZONE]
    )

    # make sur the filter include_deja_vu is false
    # to exclude the deja_vu
    users_dataset[1]['filter']['include_deja_vu'] = False

    # make sur the filter "include_deja_vu" is false
    mock_user = mocker.patch("services.user_service.UserService.get_user")
    mock_user.return_value = User.from_dict(users_dataset[1])

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}")

    # assert mock_user is called
    assert mock_user.called

    jay = await response.json()
    response_prods = jay.get('products')

    # assert list are the same
    # which means all the products of user_entries are in response_prods and vice-versa
    assert all(_p.meta.id in [k['_id'] for k in response_prods] for _p in user_entries)
    assert all(_p['_id'] in [k.meta.id for k in user_entries] for _p in response_prods)


async def test_list_include_deja_vu(test_cli, mocker, dataset):
    """The list of user's deja_vu is not excluded from the results"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    # do not exclude deja_vu
    raw_entries = data_provider.find(
        city=users_dataset[1]['filter']['city'],
        max_price=users_dataset[1]['filter']['max_price'],
    )

    # make sur the filter include_deja_vu is false
    # to exclude the deja_vu
    users_dataset[1]['filter']['include_deja_vu'] = True

    # make sur the filter "include_deja_vu" is false
    mock_user = mocker.patch("services.user_service.UserService.get_user")
    mock_user.return_value = User.from_dict(users_dataset[1])

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}")

    # assert mock_user is called
    assert mock_user.called

    jay = await response.json()
    response_prods = jay.get('products')

    # assert list are the same
    # which means all the products of user_entries are in response_prods and vice-versa
    assert all(_p.meta.id in [k['_id'] for k in response_prods] for _p in raw_entries)
    assert all(_p['_id'] in [k.meta.id for k in raw_entries] for _p in response_prods)


async def test_list_filter_city(test_cli, mocker, dataset):
    """The list is filtered according to the user's cities list pref"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    cities = users_dataset[1]['filter']['city']

    # do not exclude deja_vu
    raw_entries = data_provider.find(
        city=cities,
        max_price=users_dataset[1]['filter']['max_price'],
        exclude=users_dataset[1]['deja_vu'][ZONE]
    )

    # make sur the filter "include_deja_vu" is false
    mock_user = mocker.patch("services.user_service.UserService.get_user")
    mock_user.return_value = User.from_dict(users_dataset[1])

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}")

    # assert mock_user is called
    assert mock_user.called

    jay = await response.json()
    response_prods = jay.get('products')

    assert all(_p['city'] in cities for _p in response_prods)


async def test_list_max_price(test_cli, mocker, dataset):
    """The list is filtered according to the user's max_price pref"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    max_price = users_dataset[1]['filter']['max_price']

    # do not exclude deja_vu
    raw_entries = data_provider.find(
        city=users_dataset[1]['filter']['city'],
        max_price=max_price,
        exclude=users_dataset[1]['deja_vu'][ZONE]
    )

    # make sur the filter "include_deja_vu" is false
    mock_user = mocker.patch("services.user_service.UserService.get_user")
    mock_user.return_value = User.from_dict(users_dataset[1])

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}")

    # assert mock_user is called
    assert mock_user.called

    jay = await response.json()
    response_prods = jay.get('products')

    assert all(float(_p['price']) <= max_price for _p in response_prods)