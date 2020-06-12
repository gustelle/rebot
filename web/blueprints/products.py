# -*- coding: utf-8 -*-

import logging
import urllib
import itertools
import operator
import time

from elasticsearch import ElasticsearchException
from jsonschema import validators, Draft4Validator

import ujson as json

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args, fields
from sanic_babel import gettext

from objects import User
from services.user_service import UserService
from services.data.data_meta import CatalogMeta
from services.data.data_provider import ProductService
from services.exceptions import ServiceError

from . import products_blueprint
from .login import login_required, inject_user_info

import config
import utils

"""
Blueprints receive raw data and verify their structure (nature of fields, compliance with mandatory fields)
However, the field value checking and sanitization is not done here, rather in backend services / tasks
"""

LOGGER = logging.getLogger('app')

ITEM_SCHEMA = {
    "type": "object",
    "properties" : {
        "_id": {"type" : "string"},
        "sku": {"type" : "string"},
        "catalog": {"type" : "string"},
        "title"     : { "type" : "string", "minLength": 0}, # allow blank strings
        "description": { "type" : "string"},
        "price"     : { "type" : "number", "minimum": 0},
        "city"    : { "type" : "string"},
        "media" : {"type": "array", "items": { "type": "string" }},
        "url" : {"type" : "string"},
    },
    "required": ["_id", "sku", "catalog", "title", "price", "city", "url"],
}


@products_blueprint.route('/<id>', methods=["GET"])
@parse_query_args
async def get_product(request, id: str, zone: str = ''):
    """
    """

    if not zone or not zone.strip():
        raise InvalidUsage(f"zone must be set")

    elastic_session = ProductService(zone)
    result = elastic_session.get(id=id)

    if result is None:
        LOGGER.warning(f"document with id {id} not existing for zone '{zone}'")
        return response.json({
            'success': False,
            'errors': [f"document with id {id} not found for zone '{catazonelog}'"]
        })

    # check schema
    item = result.to_json(include_meta=True)

    v = Draft4Validator(ITEM_SCHEMA)
    errors = sorted(v.iter_errors(item), key=lambda e: e.path)
    if errors:
        LOGGER.warning(f"JSON schema error on {item}")
        return response.json({
            'success': False,
            'errors': [e.message for e in errors],
        })

    return response.json({
        'success': True,
        'result': item
    })



@products_blueprint.route('/', methods=["GET"])
@parse_query_args
async def list_products(
    request,
    zone: str,
    page: int=1,
    user_id: str='',
    city: fields.List[str]=None,
    max_price: str='',
    feature: fields.List[str]=None,
    catalog: str='',
    tbv: bool=False):
    """
    the products of a given zone

    :param zone: the geographical zone, must be a non-blank string
    :param page: current page of results
    :param user_id: optional id of the current user. The following user preferences are considered to render the results : 'deja_vu', 'tbv' and 'include_deja_vu'
    :param feature: an optional list of comma separated features
    :param city: comma separated list of cities to filter results (user prefs are not considered). When void, we consider the cities should not be considered as a filter
    :param max_price: float. When set to O, we consider the price should not be considered as a filter
    :param catalog: optional, the real estate agency on which the real estate property has been scraped. Ignored when void
    :param tbv: when set to True, only the properties marked "tbv" are listed. Defaults is False

    """

    if not zone.strip():
        raise InvalidUsage(f"zone must be set")

    # fetch user to check if it exists !!
    user = None
    if user_id:
        u_service = UserService()
        user = u_service.get_user(user_id)

    # to avoid errors during querying remove all blank items
    if feature:
        feature = [urllib.parse.unquote(item.strip()) for item in feature if item.strip()]
        LOGGER.debug(f"Filtering on feature: {feature}")

    # override user max_price
    # if not set, we consider that it's intentional and means that the max_price is 0 (no max_price)
    if not max_price or not max_price.strip():
        max_price = 0.0
    else:
        max_price = float(str(max_price))

    if not catalog.strip():
        catalog = None

        ##################################################
        # filter based on user prefs
        exclude_items = None

    try:
        exclude_items = None
        if user and not user.filter.include_deja_vu:
            exclude_items = user.deja_vu.get(zone)

        # query entries
        service = ProductService(zone)
        entries, count = service.find(
            page=page,
            city=city,
            max_price=max_price,
            exclude=exclude_items,
            feature=feature,
            catalog=catalog
        )

        results = [_entry.to_json(include_meta=True) for _entry in entries]

        LOGGER.debug(f"Filtered Results ({count} entries) : {[k.meta.id for k in entries]}")

        ##################################################
        # Mark products as deja_vu or TBV
        for x in results:
            if user and user.tbv and x['_id'] in user.tbv.get(zone):
                x['tbv']=True
            if user and user.deja_vu and x['_id'] in user.deja_vu.get(zone) and user.filter.include_deja_vu:
                x['deja_vu']=True

        ##################################################
        # eventually filter properties marked as tbv
        if tbv:
            filtered_list = []
            for x in results:
                if x.get('tbv'):
                    filtered_list.append(x)
                else:
                    count -= 1
            results = filtered_list

        ##################################################
        # map catalog info
        service = CatalogMeta()
        catalogs = dict()
        for catalog_item in service.get_catalogs():
            catalogs[catalog_item.short_name] = catalog_item.to_dict()

        # check schema of the products
        items = {
            "reps": results
        }

        ITEMS_LIST_SCHEMA = {
            "type": "object",
            "properties" : {
                "reps": {"type": "array", "items": {
                    "$ref": "#/definitions/rep" }
                }
            },
            "definitions": {
                "rep": ITEM_SCHEMA
            }
        }

        # v&rification globale pour des raisons de perf
        # vérification plus fine si erreur
        v = Draft4Validator(ITEMS_LIST_SCHEMA)
        errors = sorted(v.iter_errors(items), key=lambda e: e.path)
        if errors:

            # ne pas pénaliser l'ensemble de la réponse
            # supprimer les items qui posent probleme
            safe_list = []
            for rep in results:

                v = Draft4Validator(ITEM_SCHEMA)
                errors = sorted(v.iter_errors(rep), key=lambda e: e.path)

                if errors:
                    LOGGER.warning(f"Error in the schema of {rep}: {[e.message for e in errors]}")
                    # item is not inserted in the list
                    # withdraw it from the total count
                    count -= 1
                else:
                    safe_list.append(rep)

            # final list returned to the user
            results = safe_list

        # and refresh pagination after all the filterings
        rest = count%config.ES.RESULTS_PER_PAGE
        pages = count//config.ES.RESULTS_PER_PAGE if rest == 0 else count//config.ES.RESULTS_PER_PAGE + 1

        return response.json({
            'success': True,
            'products': results,
            'catalogs': catalogs,
            'count': count,
            'pages': pages,
            'current_page': page,
        })
    except Exception as e:
        LOGGER.error(e)
        raise ServerError(e)


###################################################################################################
# VIEWS
###################################################################################################


@products_blueprint.route('/list')
@inject_user_info
# @parse_query_args  # doesn't seem to be compatible with @inject_user_info (arg user_info is injected)
async def render_products_list(request, user: User):
    """
    This route renders a list of real estate properties

    :param user: injected, set to None if user is not authenticated
    """

    zone = request.args.get("zone") or config.ENV.DEFAULT_ZONE
    max_price = request.args.get("max_price") or 0
    city = request.args.get("city") or ''

    return await utils.render_template(
        "entries.html",
        request=request,
        zone=zone,
        user=user,
        max_price = max_price,
        city=[c for c in city.split(',') if c.strip()!='']
    )
