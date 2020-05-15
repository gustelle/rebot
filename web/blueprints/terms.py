# -*- coding: utf-8 -*-

import logging
import urllib

from sanic import response
from sanic.exceptions import abort, ServerError, InvalidUsage

from sanicargs import parse_query_args

import ujson as json

from services.exceptions import ServiceError
from services.data.data_provider import ProductService

from . import terms_blueprint

import config
import utils

LOGGER = logging.getLogger('app')


###########################################################################


@terms_blueprint.route('/<term>', methods=["GET"])
@parse_query_args
async def get_terms(request, term: str, zone: str, q: str=None):
    """
    Retreives the list of the catalogs managed by the app
    """
    results = []

    if term not in ['city', 'features']:
        raise InvalidUsage(f"unsupported term {term}")

    # some minimum checks to be reinforced
    if q:
        q = utils.safe_text(urllib.parse.unquote(q))

    service = ProductService(zone)
    results = service.get_term_facets(term, startswith=q)
    # do not return doc_count, only values
    results = [f[0] for f in results]

    return response.json({
        'success'	: True,
        'results'	: results
    })
