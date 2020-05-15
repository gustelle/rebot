# -*- coding: utf-8 -*-
import copy
import uuid
import random

import pytest

import ujson as json

from main import app

from tests.data.base_data import ZONE, CATALOG

import config


async def test_insert_delete_200(test_cli, mocker, dataset):
    """A valid REP is inserted or updated
    """
    product_dataset = copy.deepcopy(dataset['products']['valid'])

    response = await test_cli.post(
        '/reps',
        data=json.dumps({
            'catalog': CATALOG,
            'item': product_dataset[0],
            'zone': ZONE
        }),
        headers={"content-type": "application/json"})

    jay = await response.json()

    # only the first products_dataset['products'] is upserted
    assert jay['success']


async def test_allow_blank_titles(test_cli, mocker, dataset):
    """A valid REP is inserted or updated
    """
    product_dataset = copy.deepcopy(dataset['products']['valid'])
    p = product_dataset[0]
    p['title'] = ""

    response = await test_cli.post(
        '/reps',
        data=json.dumps({
            'catalog': CATALOG,
            'item': p,
            'zone': ZONE
        }),
        headers={"content-type": "application/json"})

    jay = await response.json()

    # only the first products_dataset['products'] is upserted
    assert jay['success']


async def test_schema_validation_error(test_cli, mocker, dataset):
    """An invalid REP is reported
    """
    product_dataset = copy.deepcopy(dataset['products']['invalid'])

    response = await test_cli.post(
        '/reps',
        data=json.dumps({
            'catalog': CATALOG,
            'item': product_dataset[0],
            'zone': ZONE
        }),
        headers={"content-type": "application/json"})

    jay = await response.json()

    assert jay['success'] == False
    assert "errors" in jay


def test_insert_schema_error_false(mocker, dataset):
    """
    Passing incorrect data causes a functional error
    The response status is 200, but the JSON response contains 'success:false'
    """
    invalid_product_dataset = copy.deepcopy(dataset['products']['invalid'])

    req, resp = app.test_client.post(
        '/reps',
        data=json.dumps({
                'catalog': CATALOG,
                'item': invalid_product_dataset[0],
                'zone': ZONE
            }),
        headers={"content-type": "application/json"})

    jay = resp.json
    assert not jay['success']


def test_insert_catalog_blank_400(dataset):
    """catalog, is missing, the product is not upserted
    A response status 400 is expected
    """
    product_dataset = copy.deepcopy(dataset['products']['valid'])

    req, resp = app.test_client.post(
        '/reps',
        data=json.dumps({
            'item': product_dataset[0],
            'zone': ZONE
        }),
        headers={"content-type": "application/json"})

    assert resp.status == 400


def test_insert_ZONE_blank_400(dataset):
    """ZONE is missing, the product is not upserted
    A response status 400 is expected
    """
    product_dataset = copy.deepcopy(dataset['products']['valid'])

    req, resp = app.test_client.post(
        '/reps',
        data=json.dumps({
            'item': product_dataset[0],
            'catalog': CATALOG
        }),
        headers={"content-type": "application/json"})

    assert resp.status == 400
