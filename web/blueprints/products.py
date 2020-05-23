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

from services.user_service import UserService
from services.data.data_meta import CatalogMeta
from services.data.data_provider import ProductService
from services.exceptions import ServiceError

from . import products_blueprint

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
    feature: fields.List[str]=None):
    """
    the products of a given zone

    :param zone: the geographical zone, must be a non-blank string
    :param page: current page of results
    :param user_id: id of the current user
    :param feature: an optional list of comma separated features
    :param city: when set, this list overrides the city filter of the user_id
    :param max_price: when set, this float overrides the max_price filter of the user_id
    """
    if not zone.strip():
        raise InvalidUsage(f"zone must be set")

    if not user_id:
        raise InvalidUsage(f"Inalid User")

    # fetch user to check if it exists !!
    u_service = UserService()
    user = u_service.get_user(user_id)
    if not user:
        raise InvalidUsage(f"Inalid User")

    # to avoid errors during querying remove all blank items
    if feature:
        feature = [urllib.parse.unquote(item.strip()) for item in feature if item.strip()]
        LOGGER.debug(f"Filtering on feature: {feature}")

    if max_price:
        try:
            max_price = float(max_price)
        except:
            LOGGER.warning(f"Ignored param max_price {max_price}, could not be parsed to float")
            max_price = 0.0

    # override user max_price
    if max_price and max_price > 0.0:
        user.filter.max_price = max_price
        LOGGER.debug(f"Param max_price overriden : {max_price}")

    # to avoid errors during querying remove all blank items
    if city:
        city = [urllib.parse.unquote(item.strip()) for item in city if item.strip()]
        LOGGER.debug(f"Filtering on city: {city}")

    # override user city
    if city:
        user.filter.city = city
        LOGGER.debug(f"Param city : {city}")

    ##################################################
    # filter based on user prefs
    exclude_items = None

    try:
        if not user.filter.include_deja_vu:
            exclude_items = user.deja_vu.get(zone)

        # query entries
        service = ProductService(zone)
        entries = service.find(
            page=page,
            city=user.filter.city,
            max_price=user.filter.max_price,
            exclude=exclude_items,
            feature=feature
        )
        count = service.count(
            city=user.filter.city,
            max_price=user.filter.max_price,
            exclude=exclude_items,
            feature=feature
        )

        rest = count%config.ES.RESULTS_PER_PAGE
        pages = count//config.ES.RESULTS_PER_PAGE if rest == 0 else count//config.ES.RESULTS_PER_PAGE + 1
        results = [_entry.to_json(include_meta=True) for _entry in entries]

        LOGGER.debug(f"Filtered Results ({count} entries) : {[k.meta.id for k in entries]}")

        ##################################################
        # Mark products as deja_vu or TBV
        for x in results:
            if user.tbv and x in user.tbv.get(zone):
                x['tbv']=True
            if user.deja_vu and x in user.deja_vu.get(zone) and user.filter.include_deja_vu:
                x['deja_vu']=True


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
                    # and refresh pagination
                    rest = count%config.ES.RESULTS_PER_PAGE
                    pages = count//config.ES.RESULTS_PER_PAGE if rest == 0 else count//config.ES.RESULTS_PER_PAGE + 1

                else:
                    safe_list.append(rep)

            # final list returned to the user
            results = safe_list

        return response.json({
            'success': True,
            'products': results,
            'catalogs': catalogs,
            'count': count,
            'pages': pages,
            'current_page': page,
        })
    except Exception as e:
        LOGGER.info(e)
        return response.json({})



###################################################################################################
# VIEWS
###################################################################################################


@products_blueprint.route('/list')
@parse_query_args
async def render_products_list(request, zone: str='', user_id: str=''):
    """
    This route renders a list of real estate properties
    """

    if not zone or zone.strip()=='':
        zone = config.ENV.DEFAULT_ZONE
        LOGGER.info(f"Using Default zone: {zone}")

    # fetch user to check if it exists !!
    u_service = UserService()
    user = u_service.get_user(user_id)
    if not user:
        raise InvalidUsage(f"Inalid User")

    return await utils.render_template(
        "entries.html",
        request=request,
        title=gettext('nlp_products_table_title', request),
        zone=zone,
        user=user.to_dict()
    )
