# -*- coding: utf-8 -*-
import copy
import random

from distutils.util import strtobool

import pytest

import ujson as json
from jsonschema import validators, Draft4Validator

from main import app

from services.exceptions import ServiceError
from services.data.data_meta import CatalogMeta
from services.data.data_provider import ProductService
from services.elastic_service import Product

from objects import User
import config

from tests.data.base_data import ZONE
from tests.data.products import get_product_id


ITEM_SCHEMA = {
    "type": "object",
    "properties" : {
        "id": {"type" : "string"},
        "sku": {"type" : "string"},
        "catalog": {"type" : "string"},
        "title"     : { "type" : "string", "minLength": 0}, # allow blank strings
        "description": { "type" : "string"},
        "price"     : { "type" : "number", "minimum": 0},
        "city"    : { "type" : "string"},
        "media" : {"type": "array", "items": { "type": "string" }},
        "url" : {"type" : "string"},
        "area": { "type" : "number", "minimum": 0}
    },
    "required": ["id", "sku", "catalog", "title", "price", "city", "url"],
}


async def test_get(test_cli, mocker, dataset):
    """verify the normal response"""
    training_dataset = copy.deepcopy(dataset['products']['valid'])

    data_provider = ProductService(ZONE)
    id = get_product_id(training_dataset[0])
    entry = data_provider.get(id=id)

    response = await test_cli.get(f"/products/{id}?zone={ZONE}")
    jay = await response.json()

    result = jay.get('result')
    print(f"result: {result}")
    v = Draft4Validator(ITEM_SCHEMA)
    errors = sorted(v.iter_errors(result), key=lambda e: e.path)

    assert not errors
    assert result and result['id'] == id


async def test_get_jsonschema_error(test_cli, mocker, dataset):
    """if the product is not compliant with the expected JSON schema, it is not returned"""

    # mock an invalid object returned by Elasticsearch
    training_dataset = copy.deepcopy(dataset['products']['valid'])

    id = get_product_id(training_dataset[0])

    # delete the sku which will cause the json schema validation error
    del training_dataset[0]['sku']

    mock_es = mocker.patch("services.data.data_provider.ProductService.get")
    mock_es.return_value = Product.from_dict(training_dataset[0])

    response = await test_cli.get(f"/products/{id}?zone={ZONE}")

    jay = await response.json()
    assert jay and not jay['success']


async def test_get_no_zone(test_cli, mocker, dataset):
    """zone param is required to fetch a product"""

    training_dataset = copy.deepcopy(dataset['products']['valid'])
    # product id
    id = get_product_id(training_dataset[0])

    response = await test_cli.get(f"/products/{id}?zone=")

    assert response.status == 400


async def test_list_no_user(test_cli, mocker, dataset):
    """This Usage is valid"""

    response = await test_cli.get(f"/products?zone={ZONE}")

    assert response.status == 200


async def test_list_no_zone(test_cli, mocker, dataset):
    """Invalid Usage"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])

    response = await test_cli.get(f"/products?user_id={users_dataset[0]['id']}")

    assert response.status == 400


async def test_list(test_cli, mocker, dataset):
    """Use the API /products to list the products of a catalog"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    entries, count = data_provider.find(page=1)

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}")

    jay = await response.json()

    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    response_prods = jay.get('products')

    assert sorted([k['_id'] for k in list_entries]) == sorted([k['id'] for k in response_prods])
    assert jay.get('count') == count

    catalogs = dict()
    for catalog_item in dataset['catalogs']['valid']:
        catalogs[catalog_item['short_name']] = catalog_item

    assert jay.get('catalogs') == catalogs


async def test_list_tbv(test_cli, mocker, dataset):
    """only products marked as TBV are listed"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    entries, count = data_provider.find(page=1)

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}&tbv=true")

    t = await response.text()

    print(t)

    jay = await response.json()

    # filter on TBV
    # only the products listed in the user filters "tbv" are kept
    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    list_entries = list(filter(lambda x : x['_id'] in users_dataset[1]['tbv'][ZONE], list_entries))

    response_prods = jay.get('products')

    # perfect match
    assert all(_prod['id'] in [x['_id'] for x in list_entries] for _prod in response_prods)
    assert all(_prod['_id'] in [x['id'] for x in response_prods] for _prod in list_entries)


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
    mock_find.return_value = [Product.from_dict(p) for p in training_dataset], len(training_dataset)

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}")

    jay = await response.json()

    assert jay and jay['success']
    assert len(jay['products']) == len(training_dataset)-1
    assert jay['count'] == len(training_dataset)-1


async def test_list_filter_feature(test_cli, mocker, dataset):
    """The list is filtered with a feature"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    entries, count = data_provider.find(feature=["3 chambres"])

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}&feature=3 chambres")

    jay = await response.json()

    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    response_prods = jay.get('products')

    assert all("3 chambres" in _prod['features'] for _prod in list_entries)
    assert all(_prod['id'] in [k['_id'] for k in list_entries] for _prod in response_prods)
    assert jay.get('count') == count


async def test_list_combine_features(test_cli, mocker, dataset):
    """The list is filtered with several features"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])

    data_provider = ProductService(ZONE)

    features_list = ["3 chambres", "jardin"]

    entries, count = data_provider.find(feature=features_list)

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[0]['id']}&feature={','.join(features_list)}")

    jay = await response.json()

    list_entries = list([entry.to_json(include_meta=True) for entry in entries])
    response_prods = jay.get('products')

    assert all("3 chambres" in _prod['features'] for _prod in list_entries)
    assert all("jardin" in _prod['features'] for _prod in list_entries)
    assert all(_prod['id'] in [k['_id'] for k in list_entries] for _prod in response_prods)
    assert jay.get('count') == count


async def test_list_exclude_deja_vu(test_cli, mocker, dataset):
    """Exclude deja_vu for a user"""

    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    # take user[1] (id=2) which has some deja_vu
    # and make a manual exclusion of the deja_vu
    user_entries, count = data_provider.find(
        # city=users_dataset[1]['filter']['city'],
        # max_price=users_dataset[1]['filter']['max_price'],
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
    assert all(_p.meta.id in [k['id'] for k in response_prods] for _p in user_entries)

    # print([k.meta.id for k in user_entries])
    # print("--------------------------------")
    # print([_p['_id'] for _p in response_prods])
    assert all(_p['id'] in [k.meta.id for k in user_entries] for _p in response_prods)


async def test_list_include_deja_vu(test_cli, mocker, dataset):
    """The list of user's deja_vu is not excluded from the results"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    # do not exclude deja_vu
    raw_entries, count = data_provider.find(
        # city=users_dataset[1]['filter']['city'],
        # max_price=users_dataset[1]['filter']['max_price'],
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
    assert all(_p.meta.id in [k['id'] for k in response_prods] for _p in raw_entries)
    assert all(_p['id'] in [k.meta.id for k in raw_entries] for _p in response_prods)


async def test_list_override_city(test_cli, mocker, dataset):
    """the cities list provided in param overrides the user's cities filter"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    cities = ['test1', 'test2']

    mock_find = mocker.patch("services.data.data_provider.ProductService.find")
    # mock_count = mocker.patch("services.data.data_provider.ProductService.count")

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}&city={','.join(cities)}")

    # assert mock_user is called
    find_args, find_kwargs = mock_find.call_args
    # count_args, count_kwargs = mock_count.call_args

    assert find_kwargs['city'] == cities
    # assert count_kwargs['city'] == cities


async def test_list_override_max_price(test_cli, mocker, dataset):
    """The list is filtered according to the user's max_price pref"""
    users_dataset = copy.deepcopy(dataset['users']['valid'])
    data_provider = ProductService(ZONE)

    max_price = 1

    mock_find = mocker.patch("services.data.data_provider.ProductService.find")
    # mock_count = mocker.patch("services.data.data_provider.ProductService.count")

    response = await test_cli.get(f"/products?zone={ZONE}&user_id={users_dataset[1]['id']}&max_price={max_price}")

    # assert mock_user is called
    find_args, find_kwargs = mock_find.call_args
    # count_args, count_kwargs = mock_count.call_args

    assert find_kwargs['max_price'] == max_price
    # assert count_kwargs['max_price'] == max_price
