# -*- coding: utf-8 -*-
import os
import pytest

import requests


class ElasticResponse():
    """Mock the Elastic response"""
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


async def test_200(test_cli, mocker):
    """
    """

    """the response is supposed to be a text, not an object !"""
    agg = '{\
        "aggregations": {\
            "by_date": {\
                "buckets": [\
                    {\
                        "key_as_string": "2020-12-01T12:00:00.00Z",\
                        "doc_count": 1\
                    },\
                    {\
                        "key_as_string": "2020-12-02T12:00:00.00Z",\
                        "doc_count": 2\
                    }\
                ]\
            },\
            "by_catalog": {\
                "buckets": [\
                    {\
                        "key": "cat1",\
                        "doc_count": 3\
                    },\
                    {\
                        "key": "cat2",\
                        "doc_count": 4\
                    }\
                ]\
            }\
        }\
    }'

    def positive_response(*args, **kwargs):
        return ElasticResponse(status_code=200, text=agg)

    mock_req = mocker.patch("requests.post")
    mock_req.side_effect = positive_response

    response = await test_cli.get(
        f"/monitoring",
        headers={"content-type": "application/json"}
    )

    data = await response.json()

    assert data["success"]
    assert data["result"] == {
        "count_by_date": {
            "2020-12-1": 1,
            "2020-12-2": 2
        },
        "count_by_catalog": {
            "cat1": 3,
            "cat2": 4
        }
    }


async def test_error_in_elastic_response(test_cli, mocker):
    """
    """

    """the response is supposed to be a text, not an object !"""

    def negative_response(*args, **kwargs):
        return ElasticResponse(status_code=400, text="")

    mock_req = mocker.patch("requests.post")
    mock_req.side_effect = negative_response

    response = await test_cli.get(
        f"/monitoring",
        headers={"content-type": "application/json"}
    )

    assert response.status == 500
