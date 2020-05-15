import logging
import ujson as json

import sentry_sdk
from sentry_sdk import configure_scope

import config
import utils
import settings


LOGGER = logging.getLogger("app")


def do_send_to_sentry(items, catalog, errors):
    """each item in the list of items is enriched with the catalog info, then
    the items are sent to sentry to keep track of errors
    """
    if utils.is_list(items):
        send_it = {
            "catalog": catalog,
            "items": items,
            "errors": errors
        }
        with configure_scope() as scope:
            # setting a tag "spider" enables in sentry to retrieve issues coming from spiders
            scope.set_tag("origin", "spider")
            scope.set_tag("catalog", catalog)
            sentry_sdk.capture_message(json.dumps(send_it))
        LOGGER.info(f"{len(items)} items sent to sentry on catalog {catalog}")
    else:
        LOGGER.error(f"Items passed are not a valid list")

    return True
