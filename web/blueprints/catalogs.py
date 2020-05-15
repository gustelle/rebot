# -*- coding: utf-8 -*-

import logging
import urllib

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args

from jsonschema import validators, Draft4Validator
import ujson as json

from services.data import data_meta
from services.exceptions import ServiceError

from objects import Catalog

from . import catalogs_blueprint

import config
import utils

LOGGER = logging.getLogger('app')


CATALOG_SCHEMA = {
    "type": "object",
    "properties" : {
        "id": {"type" : "string"},
        "long_name": {"type" : "string"},
        "zone" : {"type" : "string"},
        "short_name" : {"type" : "string"}
    },
    "required": ["zone", "id", "short_name"]
}


###########################################################################


@catalogs_blueprint.route('/', methods=["GET"])
@parse_query_args
async def get_catalogs(request, lang: str, zone: str):
    """
    Retreives the list of the catalogs knwon by the app

    :return: a JSON, the list of catalogs stored in the key "catalogs"
    """
    # empty strings are falsy,
    # the params lang/industry can be compliant with lang: str and be = ''
    if not lang or not lang.strip():
        lang = None
    else:
        lang = utils.safe_text(urllib.parse.unquote(lang))

    if not zone or not zone.strip():
        zone = None
    else:
        zone = utils.safe_text(urllib.parse.unquote(zone))

    service = data_meta.CatalogMeta(lang=lang, zone=zone)
    catalog_list = service.get_catalogs()

    return response.json({
        'success'	: True,
        'catalogs'	: [cat.to_dict() for cat in catalog_list]
    })


@catalogs_blueprint.route('/<short_name>', methods=["GET"])
async def get_the_catalog(request, short_name: str):
    """
    Retreives a catalog by its short_name (unique ID)

    :return: a JSON, the catalog is stored in the key "result"
    """
    short_name = urllib.parse.unquote(short_name)

    service = data_meta.CatalogMeta()
    result = service.get_the_catalog(short_name)

    return response.json({
        'success': True,
        'result': result.to_dict()
    })


@catalogs_blueprint.route('/<short_name>', methods=["POST", "PUT"])
async def add_catalog(request, short_name: str):
    """
    Registers or updates a catalog

    :return: a JSON, the stored catalog is in the key 'result'.
        If the catalog does not comply with the following Shema, the schema errors are provided in the returned JSON
        {
            "type": "object",
            "properties" : {
                "id": {"type" : "string"},
                "long_name": {"type" : "string"},
                "zone" : {"type" : "string"},
                "short_name" : {"type" : "string"}
            },
            "required": ["zone", "id", "short_name"]
        }
    """

    short_name = urllib.parse.unquote(short_name)
    json_args = json.loads(request.body)
    json_args["id"] = short_name
    json_args["short_name"] = short_name

    v = Draft4Validator(CATALOG_SCHEMA)
    errors = sorted(v.iter_errors(json_args), key=lambda e: e.path)
    if errors:
        LOGGER.error(f"JSON schema error on {json_args}")
        return response.json({
            'success': False,
            'errors': [e.message for e in errors]
        })


    try:

        service = data_meta.CatalogMeta()
        the_catalog = Catalog.from_dict(json_args)
        resp = service.register_catalog(the_catalog)
        return response.json({
            'success': resp,
            'result': the_catalog.to_dict()
        })

    except Exception as e:
        LOGGER.error(f"Failed to register catalog {json_args}, {e}")
        return response.json({
            'success': False
        })
