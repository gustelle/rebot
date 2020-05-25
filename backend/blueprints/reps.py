# -*- coding: utf-8 -*-

"""Bluepring dedicated to managing REPs (Real Estate Properties)
"""

import logging

from jsonschema import validators, Draft4Validator

import ujson as json

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args, fields
from sanic_babel import gettext

from tasks import index_items, report_error

from . import reps_blueprint

import config
import utils
import main

"""
Blueprints receive raw data and verify their structure (nature of fields, compliance with mandatory fields)
However, the field value checking and sanitization is not done here, rather in backend services / tasks
"""

LOGGER = logging.getLogger('app')


@reps_blueprint.route('/', methods=["POST"])
async def add_rep(request):
    """
    called by the spider when an item has been fetched in order to persist it in ES.
    The item is passed as JSON into the payload
    """

    json_args = json.loads(request.body)

    short_name = json_args.get('catalog', '')
    zone = json_args.get('zone', '')

    if not short_name or not short_name.strip():
        raise InvalidUsage(f"'catalog' param is mandatory")

    if not zone or not zone.strip():
        raise InvalidUsage(f"'zone' param is mandatory")

    item = json_args.get('item', {})

    ITEM_SCHEMA = {
        "type": "object",
        "properties" : {
            "sku": {"type" : "string"},
            "title"     : { "type" : "string", "minLength": 0}, # allow blank strings
            "description": { "type" : "string"},
            "price"     : { "type" : "number", "minimum": 0},
            "area"     : { "type" : "number"},
            "city"    : { "type" : "string"},
            "media" : {"type": "array", "items": { "type": "string" }},
            "url" : {"type" : "string"},
        },
        "required": ["sku", "title", "price", "city", "url", "media"]
    }

    v = Draft4Validator(ITEM_SCHEMA)
    errors = sorted(v.iter_errors(item), key=lambda e: e.path)
    if errors:
        LOGGER.warning(f"Errors receiving item: {errors}, received {item}")
        # send this business error to sentry
        # so that we can easily be notified and visualize it
        # this will facilitate the fix of the scraping issue
        job_id = report_error(
            [item],
            catalog=short_name,
            errors=[e.message for e in errors]
        )
        return response.json({
            'success': False,
            'errors': [e.message for e in errors],
            'result': {
                'job_id': job_id
            }
        })

    # data seem to be clean, we can integrate them into elastic
    job_id = index_items(
        [item],
        catalog=short_name,
        zone=zone
    )

    return response.json({
        'success': True,
        'result': {
            'job_id': job_id
        }
    })
