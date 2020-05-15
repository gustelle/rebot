# -*- coding: utf-8 -*-

import logging

from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler

import config

if config.ENV.SENTRY_URL is not None and config.ENV.SENTRY_URL!='':
    """Send logging messages to sentry.io"""
    sentry_handler = SentryHandler(config.ENV.SENTRY_URL, environment=config.ENV.SENTRY_TAG)
    sentry_handler.setLevel(logging.ERROR)
    setup_logging(sentry_handler)