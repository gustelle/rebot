# -*- coding: utf-8 -*-
import aiohttp
import aioredis
from collections import defaultdict
import logging
import os

from sanic import Sanic
from sanic_babel import Babel
from _sanic_session import Session, AIORedisSessionInterface

import ujson as json

from blueprints import (catalogs_blueprint, products_blueprint,
                        users_blueprint, terms_blueprint, areas_blueprint,
                        welcome_blueprint, login_blueprint)

from objects import User

import config
import settings
import utils


#############################################################################
# App startup

LOGGER = logging.getLogger("app")

app = Sanic('app')

""" Auth Session """

session = Session()

@app.listener('before_server_start')
async def init_user_session(app, loop) -> None:
    app.redis = await aioredis.create_redis_pool(
        config.Q.REDIS_URL
    )
    session.init_app(app, interface=AIORedisSessionInterface(app.redis))


@app.listener('before_server_start')
async def init_aiohttp_session(sanic_app, _loop) -> None:
    sanic_app.async_session = aiohttp.ClientSession()


@app.listener('after_server_stop')
async def close_aiohttp_session(sanic_app, _loop) -> None:
    await sanic_app.async_session.close()



""" Routes """

# serve the static files under /static
CWD = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
app.static('/static', os.path.sep.join([CWD, 'blueprints', 'static']))

app.register_blueprint(login_blueprint)
app.register_blueprint(welcome_blueprint)
app.register_blueprint(products_blueprint)
app.register_blueprint(catalogs_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(terms_blueprint)
app.register_blueprint(areas_blueprint)


""" i18n """
# register Babel translations
# fixes translations not found issue
app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.sep.join([CWD, 'translations'])
babel = Babel(app, configure_jinja=False)


@babel.localeselector
def get_locale(request):
    # try to guess the language from the user accept
    # header the browser transmits. The first wins.
    langs = request.headers.get('accept-language')
    if langs:
        return langs.split(';')[0].split(',')[0].replace('-', '_')


#############################################################################
# App constants

""" Data install """

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
        from services.area_service import AreaService
        from services.data import data_meta
        from objects import Catalog, User, Area

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
            cats_file_path = os.path.sep.join([CWD, 'data', 'catalogs.jsonl'])
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
            users_file_path = os.path.sep.join([CWD, 'data', 'users.jsonl'])
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


            # install areas
            areas_file_path = os.path.sep.join([CWD, 'data', 'areas.jsonl'])
            if os.path.exists(areas_file_path):

                with open(areas_file_path, "r") as _file:
                    for line in _file:
                        obj = json.loads(line)
                        zone = obj.pop("zone")
                        areas_service = AreaService(zone)
                        resp = areas_service.register_area(Area.from_dict(obj))
                        if resp:
                            LOGGER.info(f"Area : {obj} installed")
                        else:
                            LOGGER.error(f"Area : '{obj}' could not be installed")
            else:
                LOGGER.error(f"Base areas cannot be installed, file {areas_file_path} cannot be found")
