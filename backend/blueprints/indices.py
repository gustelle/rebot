# -*- coding: utf-8 -*-

import logging
import urllib

import ujson as json

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args

from sanic_babel import gettext

from . import indices_blueprint

from  search_index import ElasticCommand, IndexError
import config
import utils

LOGGER = logging.getLogger('app')


@indices_blueprint.route('/', methods=["POST"])
async def create_index(request):
    """
    """
    json_args = json.loads(request.body)
    zone = json_args.get('zone', '')

    if not zone or zone.strip()=='':
        LOGGER.error(f"zone cannot be blank, cannot create index")
        raise InvalidUsage(f"Invalid params zone '{zone}'")

    # index name must be safe 
    zone = utils.safe_text(zone)

    success = False
    try:
        ElasticCommand.create_index(zone)
        success = True
    except IndexError as i:
        LOGGER.critical(f"Index creation error for zone {zone}")

    return response.json({
        'success': success
    })


@indices_blueprint.route('/', methods=["DELETE"])
@parse_query_args
async def delete_index(request, zone: str):
    """
    """
    zone = urllib.parse.unquote(zone)

    if not zone or zone.strip()=='':
        LOGGER.error(f"zone cannot be blank, cannot delete index")
        raise InvalidUsage(f"Invalid params zone '{zone}'")

    success = False
    try:
        ElasticCommand.delete_index(zone)
        success = True
    except IndexError as i:
        LOGGER.critical(f"Deletion error for zone {zone}")

    return response.json({
        'success': success
    })
