import logging
import sentry_sdk
from sentry_sdk.integrations.rq import RqIntegration

import config

sentry_sdk.init(
    dsn=config.ENV.SENTRY_URL,
    integrations=[RqIntegration()],
    environment=config.ENV.ENVIRONMENT)
