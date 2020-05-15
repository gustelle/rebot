# -*- coding: utf-8 -*-

import logging
import datetime

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage
from sanicargs import parse_query_args

import requests
import ujson as json

from . import monitoring_blueprint

import config

LOGGER = logging.getLogger('app')


@monitoring_blueprint.route('/', methods=["GET"])
@parse_query_args
async def monitor(request):
    """
    """

    service_up = False
    result = {}
    try:

        # do sthg
        service_up = True
        headers = {'Content-type': 'application/json'}
        data = '{\
          "aggs" : {\
                "by_date" : {\
                    "date_histogram" : {\
                        "field" : "created",\
                        "interval" : "day"\
                    }\
                }\
            }\
        }'

        elastic_resp = requests.post(f"{config.ES.ES_HOST}/_search?size=0", headers=headers, data=data)
        if elastic_resp.status_code >=200 and elastic_resp.status_code < 300:
            by_dates = {}
            for bucket in json.loads(elastic_resp.text)['aggregations']['by_date']['buckets']:
                d = datetime.datetime.strptime( bucket['key_as_string'], "%Y-%m-%dT%H:%M:%S.%fZ" )
                by_dates[f"{d.year}-{d.month}-{d.day}"] = bucket['doc_count']
            result['count_by_date'] = by_dates
        else:
            LOGGER.error(f"Bad response status for aggregation by_date : {elastic_resp.status_code}")
            raise ServerError("Bad response for request")

        data = '{\
            "aggs" : {\
                "by_catalog" : {\
                    "terms" : { "field" : "catalog" }\
                }\
            }\
        }'
        elastic_resp = requests.post(f"{config.ES.ES_HOST}/_search?size=0", headers=headers, data=data)
        if elastic_resp.status_code >=200 and elastic_resp.status_code < 300:
            by_catalog = {}
            for bucket in json.loads(elastic_resp.text)['aggregations']['by_catalog']['buckets']:
                by_catalog[bucket['key']] = bucket['doc_count']
            result['count_by_catalog'] = by_catalog
        else:
            LOGGER.error(f"Bad response status for aggregation by_catalog : {elastic_resp.status_code}")
            raise ServerError("Bad response for request")

    except Exception as e:
        LOGGER.error(e, exc_info=True)
        raise ServerError(e)

    return response.json({
        'success': service_up,
        'result': result
    })
