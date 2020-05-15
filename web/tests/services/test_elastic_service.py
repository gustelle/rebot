# -*- coding: utf-8 -*-
import os
import copy
from datetime import datetime

import pytest

import ujson as json

from elasticsearch_dsl import Document
from services.elastic_service import ElasticSession, Serializable

from tests.data.base_data import ZONE

import config


@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestElasticSession(object):
    """Check the params passed to Elasticsearch framework"""

    async def test_get(test_cli, mocker, dataset):
        mock_get = mocker.patch("elasticsearch_dsl.Document.get")

        session = ElasticSession(hosts=[os.getenv('ES_HOST')], zone=ZONE)
        session.get(Document, id="1")
        args, kwargs = mock_get.call_args

        assert kwargs['index'] == ZONE
        assert kwargs['id'] == "1"
        assert kwargs['doc_type'] == "_doc"
        assert kwargs['ignore'] == 404


    async def test_search(test_cli, mocker, dataset):
        mock_search = mocker.patch("elasticsearch_dsl.Document.search")

        session = ElasticSession(hosts=[os.getenv('ES_HOST')], zone=ZONE)
        session.search(Document)
        args, kwargs = mock_search.call_args

        assert kwargs['index'] == ZONE


@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestSerializable(object):
    """
    """
    async def test_from_dict(test_cli, mocker, dataset):
        doc = {
            "_index": ZONE,
            "_id": "1",
            "_routing": "elasticsearch",
            "city": "Amsterdam",
        }
        obj = Serializable.from_dict(doc)

        assert obj.meta.index == ZONE
        assert obj.meta.id == "1"
        assert obj.meta.routing == "elasticsearch"
        assert obj.city == "Amsterdam"


    async def test_to_json(test_cli, mocker, dataset):
        now = datetime.now()
        doc = {
            "_index": ZONE,
            "_id": "1",
            "_routing": "elasticsearch",
            "city": "Amsterdam",
            "created": now
        }
        obj = Serializable.from_es({'_source': doc})
        json = obj.to_json()

        assert isinstance(json, dict)
        assert json["city"] == "Amsterdam"
        assert isinstance(json["created"], str)
        assert datetime.strptime(json["created"], "%Y-%m-%dT%H:%M:%S.%f") == now  #2020-04-30T16:51:20.525003


    async def test_to_json_include_meta(test_cli, mocker, dataset):
        """NB : _index meta is not returned by the to_dict() method of elasticsearch_dsl"""
        now = datetime.now()
        doc = {
            "_index": ZONE,
            "_id": "1",
            "_routing": "elasticsearch",
            "city": "Amsterdam",
            "created": now
        }
        obj = Serializable.from_es({'_source': doc})
        json = obj.to_json(include_meta=True)

        assert isinstance(json, dict)
        assert json["city"] == "Amsterdam"
        assert json["_id"] == "1"
        assert json["_routing"] == "elasticsearch"
        assert isinstance(json["created"], str)
        assert datetime.strptime(json["created"], "%Y-%m-%dT%H:%M:%S.%f") == now  #2020-04-30T16:51:20.525003
