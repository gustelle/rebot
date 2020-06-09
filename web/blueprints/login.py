# -*- coding: utf-8 -*-
import os
import functools
import logging
import urllib

from sanic import response
from sanic.response import redirect
from sanic.exceptions import abort, ServerError, InvalidUsage
from sanic.log import error_logger
from sanic_oauth.providers import GoogleClient
from sanic_babel import gettext

from objects import User
from services.user_service import UserService

from . import login_blueprint

import config
import utils

LOGGER = logging.getLogger('app')


async def _fetch_user_info(request):
    """ Fetch user info and sync info in Firebase

    :return User: a user object
    """
    client = GoogleClient(
        request.app.async_session,
        client_id=config.OAUTH.GOOGLE_CLIENT_ID,
        client_secret=config.OAUTH.GOOGLE_CLIENT_SECRET,
        access_token=request.ctx.session['session']['token']
    )
    user, info = await client.user_info()

    # sync firebase with the user info provided
    user_service = UserService()
    u_object = user_service.save_partial(
        user.id,
        firstname=user.first_name,
        lastname=user.last_name
    )
    return u_object


@login_blueprint.route('/oauth')
async def oauth(request):

    client = GoogleClient(
        request.app.async_session,
        client_id=config.OAUTH.GOOGLE_CLIENT_ID,
        client_secret=config.OAUTH.GOOGLE_CLIENT_SECRET
    )
    if 'code' not in request.args:
        return redirect(client.get_authorize_url(
            scope='email profile',
            redirect_uri=config.OAUTH.OAUTH_REDIRECT_URI
        ))
    token, data = await client.get_access_token(
        request.args.get('code'),
        redirect_uri=config.OAUTH.OAUTH_REDIRECT_URI
    )
    request.ctx.session['session']['token'] = token
    return redirect('/welcome')


def login_required(fn):
    """auth decorator
    call function(request, user: <User object>)

    redirects to config.OAUTH.OAUTH_REDIRECT_PATH if user is not authenticated
    otherwise injects User into the function
    """

    async def wrapped(request, **kwargs):

        if 'token' not in request.ctx.session['session']:
            LOGGER.info(f"redirecting to {config.OAUTH.OAUTH_REDIRECT_PATH}")
            return redirect(config.OAUTH.OAUTH_REDIRECT_PATH)
        else:
            LOGGER.debug(f"token: {request.ctx.session['session']['token']}")

        try:
            user = await _fetch_user_info(request)
            return await fn(request, user, **kwargs)
        except Exception as exc:
            LOGGER.error(f"Error fetching user info", exc)
            return redirect(config.OAUTH.OAUTH_REDIRECT_PATH)

    return wrapped


def inject_user_info(fn):
    """auth decorator
    call function(request, user: <User object>)

    Injects None if user is not authenticated, otherwise injects User
    """

    async def wrapped(request, **kwargs):

        if 'token' in request.ctx.session['session']:
            try:
                user = await _fetch_user_info(request)
                return await fn(request, user, **kwargs)
            except Exception as exc:
                LOGGER.error(f"Error fetching user info", exc)
                return await fn(request, None, **kwargs)

        return await fn(request, None, **kwargs)

    return wrapped


@login_blueprint.route('/')
@login_required
async def redirect_to_login(request, user: User):
    return redirect(config.OAUTH.REDIRECT_AFTER_AUTH)
