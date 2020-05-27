# -*- coding: utf-8 -*-

import logging
import urllib

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args

import ujson as json

from services.area_service import AreaService
from services.exceptions import ServiceError

from . import areas_blueprint

import config
import utils

LOGGER = logging.getLogger('app')


###########################################################################


@areas_blueprint.route('/', methods=["GET"])
@parse_query_args
async def list_areas(request, zone: str):
    """
    Retreives the list of defined areas
    """
    if not zone or not zone.strip():
        raise InvalidUsage(f"zone must be set")

    service = AreaService(zone)
    results = [item.to_dict() for item in service.get_areas()]

    return response.json({
        'success'	: True,
        'results'	: results
    })
