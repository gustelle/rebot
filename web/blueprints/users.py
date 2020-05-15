# -*- coding: utf-8 -*-

import logging
import urllib

from jsonschema import validators, Draft4Validator


from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage, NotFound

from sanicargs import parse_query_args

import ujson as json

from objects import User
from services import user_service
from tasks import cleanup_user

from . import users_blueprint

import config
import utils

LOGGER = logging.getLogger('app')


def get_user_schema(zone):
    """Schema depends on the zone"""

    return {
        "type": "object",
        "definitions": {
            "filter": {
                "type": "object",
                "properties": {
                    "include_deja_vu": { "type": "boolean" },
                    "city": { "type": "array" },
                    "max_price": { "type": "number" }
                }
            },
            "zonedlist": {
                "type": "object",
                "properties": {
                    zone: { "type": "array"}
                }
            }
        },
        "properties" : {
            "id": {"type" : "string", "minLength": 1},
            "firstname": {"type" : "string"},
            "lastname": {"type" : "string"},
            "tbv": { "$ref": "#/definitions/zonedlist" },
            "deja_vu": { "$ref": "#/definitions/zonedlist" },
            "filter": { "$ref": "#/definitions/filter" }
        },
        "required": ["id"]
    }

###########################################################################


@users_blueprint.route('/<id>', methods=["GET"])
async def get_the_user(request, id: str):
    """
    Retreives a user

    the user fields are all strings, arrays are provided as comma-separated values
    """

    service = user_service.UserService()
    result = service.get_user(id)

    if not result:
        raise NotFound(f"User {id} not found")

    return response.json({
        'success': True,
        'result': result.to_dict()
    })


@users_blueprint.route('/<id>', methods=["POST", "PUT"])
@parse_query_args
async def put_user(request, id: str, zone: str):
    """
    Registers or updates a user

    the data passed in the body are expected to comply with ITEM_SCHEMA

    NB : list of values must be passed as comma separated lists, for example : city1, city2 and not [city1, city2]
    """

    if not id.strip():
        raise InvalidUsage(f"id must be set")

    if not zone or not zone.strip():
        raise InvalidUsage(f"zone must be set")

    user_dict = json.loads(request.body)
    user_dict['id'] = str(id)
    LOGGER.debug(f"user from the body: {user_dict}")

    # check schema
    v = Draft4Validator(get_user_schema(zone))
    errors = sorted(v.iter_errors(user_dict), key=lambda e: e.path)
    if errors:
        LOGGER.error(f"JSON schema error on {user_dict}")
        return response.json({
            'success': False,
            'errors': [e.message for e in errors],
        })

    # negative value of max_price means no filter
    # trick to make JSON Schema validation work in case the user does not set a max_price
    filter = user_dict.get('filter')
    if filter and filter.get('max_price') and float(filter.get('max_price')) < 0:
        del user_dict['filter']['max_price']

    # a return flag
    resp = False
    job_id = ''

    service = user_service.UserService()
    user = service.get_user(id)

    if user:
        LOGGER.debug(f"user found, {user.to_dict()}")
        # update the existing one
        # if a value is not passed in the user_dict, the old one will be kept
        existing_user = user.to_dict()
        existing_user.update(user_dict)
        user_dict = existing_user

    the_u = User.from_dict(user_dict)
    resp = service.save_user(the_u)
    LOGGER.debug(f"Saved user, {the_u.to_dict()}")


    try:
        # trigger a cleanup task of the user prefs in background
        # some properties may be obsolete in the fileds "tbv" or "deja_vu"
        job_id = cleanup_user(zone, id)
        return response.json({
            'success': resp.to_dict(),
            'result': {
                'job_id': job_id
            }
        })

    except Exception as e:
        LOGGER.warning(f"Could not proceed to user cleanup, {e}")
        return response.json({
            'success': resp.to_dict(),
            'result': {}
        })
