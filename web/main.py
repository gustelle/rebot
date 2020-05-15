# -*- coding: utf-8 -*-
import os
import logging
from collections import defaultdict

import ujson as json
from sanic import Sanic

from sanic_babel import Babel

from blueprints import (catalogs_blueprint, products_blueprint,
                        users_blueprint, terms_blueprint)

from objects import User

import config
import settings
import utils


#############################################################################
# App startup

app = Sanic('app')

# serve the static files under /static
CWD = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
app.static('/static', os.path.sep.join([CWD, 'blueprints', 'static']))

app.register_blueprint(products_blueprint)
app.register_blueprint(catalogs_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(terms_blueprint)

# register Babel translations
# fixes translations not found issue
app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.sep.join([CWD, 'translations'])
babel = Babel(app, configure_jinja=False)


@babel.localeselector
def get_locale(request):
    # if a user is logged in, use the locale from the user settings
    if request.get('current_user') is not None:
        return request['current_user'].lang
    # otherwise try to guess the language from the user accept
    # header the browser transmits. The first wins.
    langs = request.headers.get('accept-language')
    if langs:
        return langs.split(';')[0].split(',')[0].replace('-', '_')


@babel.timezoneselector
def get_timezone(request):
    if request.get('current_user') is not None:
        return request['current_user'].timezone

#############################################################################
# App constants
LOGGER = logging.getLogger("app")

"""
Data installation
"""

@app.listener('after_server_start')
async def register_base_data(app, loop):
    """
    Some base data are required for the app to run

    if the setting INSTALL_BASE_DATA is 1 in the .env file, this function will run
    this setting may need to be set to 0 for QA or CI for instance
    """

    if config.ENV.INSTALL_BASE_DATA:
        # put a semaphore to tell the other servers that this app is installing data
        # no need for the other servers to process this code
        import datetime
        from services.firebase_service import FirebaseService
        from services.user_service import UserService
        from services.data import data_meta
        from objects import Catalog

        install_me = True

        # check the timestamp and set a semaphore
        raw_service = FirebaseService() # no need to indicate a connection ID, connection ID is used by a pool manager
        timestamp = raw_service.get_value("timestamp")

        if timestamp:
            # verify if the timestamp is obsolete
            try:
                semaphore_date = datetime.datetime.fromtimestamp(float(timestamp))
                timeout_seconds = datetime.timedelta(seconds=config.ENV.INSTALLATION_TIMESTAMP_TIMEOUT)

                if ( config.ENV.INSTALLATION_TIMESTAMP_TIMEOUT==0 or semaphore_date > datetime.datetime.utcnow()-timeout_seconds ):
                    install_me = False

            except Exception as e:
                LOGGER.error(e)

        if install_me:
            # install base data
            raw_service.set_value("timestamp", datetime.datetime.utcnow().timestamp())

            # install catalogs
            cats_file_path = os.path.sep.join([CWD, 'data', 'catalogs.jl'])
            if os.path.exists(cats_file_path):

                cat_service = data_meta.CatalogMeta()
                with open(cats_file_path, "r") as cats_file:
                    for line in cats_file:
                        obj = json.loads(line)
                        the_catalog = Catalog.from_dict(obj)
                        resp = cat_service.register_catalog(the_catalog)
                        if resp:
                            LOGGER.info(f"Catalog : '{the_catalog.short_name}' installed")
                        else:
                            LOGGER.error(f"Catalog : '{the_catalog.short_name}' could not be installed")
            else:
                LOGGER.error(f"Base catalogs cannot be installed, file {cats_file_path} cannot be found")


            # install users
            users_file_path = os.path.sep.join([CWD, 'data', 'users.jl'])
            if os.path.exists(users_file_path):

                u_service = UserService()
                with open(users_file_path, "r") as users_file:
                    for line in users_file:
                        obj = json.loads(line)
                        resp = u_service.save_user(User.from_dict(obj))
                        if resp:
                            LOGGER.info(f"User : {obj} installed")
                        else:
                            LOGGER.error(f"User : '{obj}' could not be installed")
            else:
                LOGGER.error(f"Base users cannot be installed, file {users_file_path} cannot be found")
