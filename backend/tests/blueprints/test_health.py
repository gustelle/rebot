# -*- coding: utf-8 -*-
import os
import pytest

from tests.data.base_data import ZONE, CATALOG


async def test_health_200(test_cli):
    """
    standard response

    """
    response = await test_cli.get(
        f"/health?zone={ZONE}",
        headers={"content-type": "application/json"}
    )

    data = await response.json()

    assert data['success']
    assert data['result']['status'] in ['green', 'yellow', 'red']


async def test_health_400_without_context(test_cli):
    """
    """
    response = await test_cli.get(
        f"/health?zone=",
        headers={"content-type": "application/json"}
    )

    assert response.status == 400


async def test_health_elastic_not_responding_200(test_cli, monkeypatch):
    """
    elasticsearch is not responding
    """

    monkeypatch.setattr('config.ES.ES_HOST', 'http://myhost:1234')

    response = await test_cli.get(
        f"/health?zone={ZONE}",
        headers={"content-type": "application/json"}
    )

    data = await response.json()

    assert not data['success']
    # remove the patch !!
    monkeypatch.setattr('config.ES.ES_HOST', os.getenv('ES_HOST'))
