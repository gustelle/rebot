# -*- coding: utf-8 -*-

import copy
import pytest
import ujson as json

from main import app

import utils
import config

from objects import Catalog


async def test_add(test_cli, dataset, pyrebase_db, firebase_root_node):
    """JSON schema validation
    """
    catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
    catalog_dataset[0]['short_name'] = 'mycat'  # do not override the dataset which is used by other tests !

    short_name = catalog_dataset[0]['short_name']
    zone = catalog_dataset[0]['zone']
    long_name = catalog_dataset[0]['long_name']

    body = {
        "zone": zone,
        "long_name": long_name
    }

    response = await test_cli.post(
        f"/catalogs/{short_name}",
        data=json.dumps(body),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay['success']

    expected_result = Catalog.from_dict(catalog_dataset[0]).to_dict()
    assert jay['result'] == expected_result

    response = await test_cli.get(f"/catalogs/{short_name}")
    jay = await response.json()

    assert jay == {
        'success': True,
        'result': expected_result
    }

    # delete the catalog for other tests
    pyrebase_db.child(firebase_root_node).child('catalogs/mycat').remove()


async def test_add_jsonschema_error(test_cli, dataset):
    """JSON schema validation, missing zone
    """
    catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
    catalog_dataset[0]['short_name'] = 'mycat'  # do not override the dataset which is used by other tests !

    short_name = catalog_dataset[0]['short_name']
    long_name = catalog_dataset[0]['long_name']

    body = {
        # "zone": zone,
        "long_name": long_name
    }

    response = await test_cli.post(
        f"/catalogs/{short_name}",
        data=json.dumps(body),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert not jay['success']
    # the first error message contains the word "zone"
    assert 'errors' in jay and "zone" in jay['errors'][0]
