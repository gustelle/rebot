# -*- coding: utf-8 -*-

import logging
import urllib

from jsonschema import validators, Draft4Validator


from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage, NotFound

from sanicargs import parse_query_args

import ujson as json

from objects import User, UserFilter
from services import user_service
import tasks

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
                    "city": { "type": "array", "items": {"type": "string"}},
                    "max_price": { "type": "number" },
                    "area": { "type": "string" }
                }
            },
            "zonedlist": {
                "type": "object",
                "properties": {
                    zone: { "type": "array", "items": {"type": "string"}}
                }
            }
        },
        "properties" : {
            "id": {"type" : "string", "minLength": 1},
            "firstname": {"type" : "string", "minLength": 0},
            "lastname": {"type" : "string", "minLength": 0},
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
async def put_user(request, id: str, zone: str, partial: bool=True):
    """
    Registers or updates a user

    the data passed in the body are expected to comply with ITEM_SCHEMA

    :param partial: boolean, if set to false, existing user will be overriden, otherwise updates only the fields passed. Defaults to True

    NB : list of values must be passed as comma separated lists, for example : city1, city2 and not [city1, city2]
    """
    if not id.strip():
        raise InvalidUsage(f"id must be set")

    if not zone or not zone.strip():
        raise InvalidUsage(f"zone must be set")

    user_info = json.loads(request.body)
    user_info['id'] = str(id)

    # check schema
    v = Draft4Validator(get_user_schema(zone))
    errors = sorted(v.iter_errors(user_info), key=lambda e: e.path)
    if errors:
        LOGGER.error(f"JSON schema error on {user_info}")
        return response.json({
            'success': False,
            'errors': [e.message for e in errors],
        })

    # negative value of max_price means no filter
    # trick to make JSON Schema validation work in case the user does not set a max_price
    filter = user_info.get('filter')
    if filter and filter.get('max_price') and float(filter.get('max_price')) < 0:
        del user_info['filter']['max_price']

    service = user_service.UserService()

    if partial:
        # be careful, do not inject 'id' in **user_info otherwise arg 'id' is set twice
        id = user_info['id']
        del user_info['id']

        # be careful, userfilter must be an object
        if filter:
            user_info['filter'] = UserFilter(filter)

        service.save_partial(id, **user_info)
    else:
        service.save_user(User.from_dict(user_info))

    try:
        # trigger a cleanup task of the user prefs in background
        # some properties may be obsolete in the fileds "tbv" or "deja_vu"
        job_id = tasks.cleanup_user(zone, id)
        return response.json({
            'success': True,
            'result': {
                'job_id': job_id
            }
        })
    except Exception as e:
        LOGGER.warning(f"Could not proceed to user cleanup, {e}")
        return response.json({
            'success': False,
            'result': {}
        })
