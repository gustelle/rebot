# -*- coding: utf-8 -*-

import pytest
import ujson as json

from search_index import IndexError
from tests.data.base_data import ZONE


async def test_create_index(test_cli, mocker):
    """
    """

    mock_create = mocker.patch("search_index.ElasticCommand.create_index")
    mock_create.return_value = True

    response = await test_cli.post(
        '/indices',
        data=json.dumps({
            'zone': ZONE
        }),
        headers={"content-type": "application/json"})

    jay = await response.json()
    assert jay["success"]


async def test_create_index_unsafe_zone(test_cli, mocker):
    """Zone information is processed to be safe
    """

    mock_create = mocker.patch("search_index.ElasticCommand.create_index")
    mock_create.return_value = True

    response = await test_cli.post(
        '/indices',
        data=json.dumps({
            'zone': "? _.my#zone"
        }),
        headers={"content-type": "application/json"})

    args, kwargs = mock_create.call_args

    jay = await response.json()
    assert jay["success"]
    assert args[0] == "myzone"


async def test_create_index_no_zone(test_cli, mocker):
    """
    """

    mock_create = mocker.patch("search_index.ElasticCommand.create_index")
    mock_create.return_value = True

    response = await test_cli.post(
        '/indices',
        data=json.dumps({
        }),
        headers={"content-type": "application/json"})

    assert response.status == 400


async def test_index_exists(test_cli, mocker):
    """
    """

    mock_create = mocker.patch("search_index.ElasticCommand.create_index")
    mock_create.side_effect = IndexError('Boom!')

    response = await test_cli.post(
        '/indices',
        data=json.dumps({
            'zone': ZONE
        }),
        headers={"content-type": "application/json"})

    jay = await response.json()
    assert jay["success"] == False


async def test_delete_index(test_cli, mocker):
    """
    """

    mock_create = mocker.patch("search_index.ElasticCommand.delete_index")

    response = await test_cli.delete(
        f"/indices?zone={ZONE}",
        headers={"content-type": "application/json"})

    jay = await response.json()
    assert jay["success"]


async def test_delete_index_no_zone(test_cli, mocker):
    """
    """

    mock_create = mocker.patch("search_index.ElasticCommand.delete_index")

    response = await test_cli.delete(
        f"/indices",
        headers={"content-type": "application/json"})

    assert response.status == 400


async def test_delete_index_error(test_cli, mocker):
    """
    """

    mock_create = mocker.patch("search_index.ElasticCommand.delete_index")
    mock_create.side_effect = IndexError('Boom!')

    response = await test_cli.delete(
        f"/indices?zone={ZONE}",
        headers={"content-type": "application/json"})

    jay = await response.json()
    assert jay["success"] == False
