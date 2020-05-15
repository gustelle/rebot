# -*- coding: utf-8 -*-

import logging
import urllib

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args

from . import health_blueprint

from search_index import ElasticMonitoring, MonitoringError
import config
import utils

LOGGER = logging.getLogger('app')


@health_blueprint.route('/', methods=["GET"])
@parse_query_args
async def health(request, zone: str):
    """
    """

    if not zone or zone.strip()=='':
        LOGGER.error(f"zone cannot be blank, cannot check the index")
        raise InvalidUsage(f"Invalid params zone '{zone}'")

    service_up = False
    result = {}

    try:

        result = ElasticMonitoring.monitor(zone)
        service_up = True

    except MonitoringError as ese:
        LOGGER.error(f"Error monitoring the zone {zone}", exc_info=True)

    return response.json({
        'success': service_up,
        'result': result
    })
