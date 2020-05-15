import copy
import uuid

import pytest
from unittest.mock import patch

from elasticsearch import Elasticsearch, ElasticsearchException, NotFoundError

from tests.data.base_data import ZONE

from search_index import (
    ElasticSession, ElasticMonitoring, MonitoringError,
    ElasticCommand, IndexError, SearchError, _DOCUMENT_TYPE)

import config


@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestElasticSession(object):
    """
    """
    def test_init_no_ZONE(self, monkeypatch, mocker, dataset):
        """raise a ValueError in the __init__, the host is even not considered
        """
        with pytest.raises(ValueError) as c:
            ElasticSession("fake_host", "")


    def test_init_not_a_valid_host(self, monkeypatch, mocker, dataset):
        """raise a MonitoringError
        """
        with pytest.raises(MonitoringError) as c:
            session = ElasticSession("fake_host", ZONE)
            session.health()


    def test_index_args(self, monkeypatch, mocker, dataset):
        """raise a MonitoringError
        """
        mock_es = mocker.patch("elasticsearch.Elasticsearch.index")

        session = ElasticSession("fake_host", ZONE)
        session.save("1", {"key": "value"}, force_refresh=True)

        args, kwargs = mock_es.call_args

        assert 'id' in kwargs and kwargs['id'] == "1"
        assert 'body' in kwargs and kwargs['body'] == {"key": "value"}
        assert 'refresh' in kwargs and kwargs['refresh'] == True


    def test_get_args(self, monkeypatch, mocker, dataset):
        """
        """
        mock_es = mocker.patch("elasticsearch.Elasticsearch.get")

        session = ElasticSession("fake_host", ZONE)
        session.get("1")

        args, kwargs = mock_es.call_args

        assert kwargs == {
            'doc_type': _DOCUMENT_TYPE,
            'index': ZONE,
            'id': "1"
        }


    def test_get_id_not_found(self, monkeypatch, mocker, dataset):
        """
        """
        mock_es = mocker.patch("elasticsearch.Elasticsearch.get")
        mock_es.side_effect = NotFoundError()

        session = ElasticSession("fake_host", ZONE)
        obj = session.get("1")

        assert obj == None


    def test_delete_date_range_args(self, monkeypatch, mocker, dataset):
        """
        """
        mock_es = mocker.patch("elasticsearch.Elasticsearch.delete_by_query")

        session = ElasticSession("fake_host", ZONE)
        session.delete_date_range("my_field", 3)

        args, kwargs = mock_es.call_args

        assert kwargs == {
            "index": ZONE,
            "doc_type": _DOCUMENT_TYPE,
            "body": {
                "query": {
                    "range": {
                        "my_field": {
                            "lte": f"now-3d"
                        }
                    }
                }
            }
        }


    def test_delete_date_missing_date_field(self, monkeypatch, mocker, dataset):
        """
        """
        with pytest.raises(SearchError) as c:
            session = ElasticSession("fake_host", ZONE)
            session.delete_date_range("", 3)


    def test_delete_date_missing_max_days(self, monkeypatch, mocker, dataset):
        """
        """
        with pytest.raises(SearchError) as c:
            session = ElasticSession("fake_host", ZONE)
            session.delete_date_range("myfield", "")



@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestElasticMonitoring(object):
    """
    """
    def test_no_ZONE(self, monkeypatch, mocker, dataset):
        """raise a ValueError
        """
        with pytest.raises(MonitoringError) as c:
            ElasticMonitoring.monitor("")


@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestElasticCommand(object):
    """
    """
    def test_get_no_ZONE(self, monkeypatch, mocker, dataset):
        """raise a ValueError
        """
        with pytest.raises(SearchError) as c:
            ElasticCommand.get("", "1")


    def test_get_not_found(self, monkeypatch, mocker, dataset):
        """return None
        """
        ElasticCommand.get(ZONE, "1")
        mock_es = mocker.patch("search_index.ElasticSession.get")
        mock_es.return_value = None

        ElasticCommand.get(ZONE, "1")


    def test_get_args(self, monkeypatch, mocker, dataset):
        """
        """
        mock_es = mocker.patch("search_index.ElasticSession.get")

        ElasticCommand.get(ZONE, "1")

        args, kwargs = mock_es.call_args

        assert args == ("1",)


    def test_save_no_ZONE(self, monkeypatch, mocker, dataset):
        """raise a ValueError
        """
        with pytest.raises(IndexError) as c:
            ElasticCommand.save("", "1", {"key": "value"}, force_refresh=True)


    def test_save_args(self, monkeypatch, mocker, dataset):
        """
        """
        mock_es = mocker.patch("search_index.ElasticSession.save")

        ElasticCommand.save(ZONE, "1", {"key": "value"}, force_refresh=True)

        args, kwargs = mock_es.call_args

        assert args[0] == "1"
        assert args[1] == {"key": "value"}
        assert 'force_refresh' in kwargs and kwargs['force_refresh'] == True
