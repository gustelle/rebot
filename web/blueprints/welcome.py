# -*- coding: utf-8 -*-
import os
import functools
import logging
import urllib

from sanic import response
from sanic_babel import gettext

from objects import User

from . import welcome_blueprint
from .login import inject_user_info

import config
import utils

LOGGER = logging.getLogger('app')


@welcome_blueprint.route('/')
@inject_user_info
async def render_welcome(request, user: User):
    return await utils.render_template(
        "welcome.html",
        request=request,
        user=user
    )
