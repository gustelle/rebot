# -*- coding: utf-8 -*-
import os
import logging

from sanic import Sanic

from blueprints import (health_blueprint, indices_blueprint,
                        reps_blueprint, monitoring_blueprint)

import config
import settings


#############################################################################
# App startup

app = Sanic('app')

app.register_blueprint(reps_blueprint)
app.register_blueprint(health_blueprint)
app.register_blueprint(indices_blueprint)
app.register_blueprint(monitoring_blueprint)

LOGGER = logging.getLogger('app')
LOGGER.info("----- App started ------")
