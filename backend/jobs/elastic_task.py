# -*- coding: utf-8 -*-
import math
import numbers
from datetime import datetime
import logging

from search_index import ElasticCommand, IndexError
from nlp import FeaturesExtractor

import config
import utils

# import to import settings to init logging
import settings

LOGGER = logging.getLogger("app")


def do_cleanup(zones_list, max_days):
    """
    fetches real estate ads of the given zones list and deletes the ones where scraping_end_date-now() > max_days
    this enables to maintain an index without obsolete ads

    Items without scraping_end_date are deleted automatically
    """
    LOGGER.info(f"*** Cleanup task triggered for zones_list={zones_list}, max_days={max_days}")

    if not zones_list or not utils.is_list(zones_list):
        LOGGER.warning(f"No cleanup will be performed, no zones passed")
        raise ValueError("zones_list must be passed as a list")

    if not max_days or not isinstance(max_days, numbers.Integral):
        LOGGER.warning(f"No cleanup will be performed, max_days not a valid integer")
        raise ValueError("max_days must be an integer")

    result = {}
    for _zone in zones_list:
        res = ElasticCommand.delete_date_range(_zone, "scraping_end_date", max_days)
        LOGGER.info(f"Cleanup task deleted {res} documents on zone {_zone}")
        result[_zone] = res

    return result


def do_index(products_list, catalog, zone):
    """
    performs async indexation of real estate properties.

    Tasks are allowed to index silly data, thus,
    so that a max of data is scraped and users can fix data issues later.

    'zone' is required, because it is used to define the index name in elastic
    """

    class TaskResult:
        """ensure a good consistency of task result"""
        def __init__(self):
            self.created = 0
            self.updated = 0
            self.errors = 0

        def increment_errors(self, value):
            self.errors += value

        def increment_created(self, value):
            self.created += value

        def increment_updated(self, value):
            self.updated += value

        def values(self):
            return {
                'created': self.created,
                'updated': self.updated,
                'errors': self.errors
            }

    result = TaskResult()

    try:

        # basic validation checks before entering the task core logic
        if not products_list or not utils.is_list(products_list):
            LOGGER.warning(f"Nothing to index on zone '{zone}', task bypass")
            raise ValueError("items must be passed as a list")

        if not zone or zone.strip()=='':
            LOGGER.error(f"Impossible to index data without zone, {len(products_list)} REPs in error")
            result.increment_errors(len(products_list))
            raise ValueError("zone cannot be blank")

        for product_dict in products_list:

            if "sku" not in product_dict or product_dict["sku"].strip()=="":
                LOGGER.error(f"SKU required to save {product_dict}, skipped")
                result.increment_errors(1)
                continue

            # enrich the product with mandatory attributes
            product_dict['catalog'] = catalog

            # identify features
            if 'description' in product_dict:
                extractor = FeaturesExtractor(product_dict['description'])
                product_dict['features'] = extractor.extract()

            # sanitize some fields, because scraping leads to unclean data
            # for fields that are used in faceting
            # replace special chars with a blank space, redundant blank spaces will be removed afterwards
            # product_dict['city'] = utils.safe_text(product_dict['city'], replace_with=" ", strict=False)

            try:

                # ensure uniqueness of the doc id
                # two properties of 2 different catalogs may have the same sku
                # need to have a safe id,
                #   because some chars like ':' are used to associate the id with user prefs in the frontend
                doc_id = utils.safe_text(f"{catalog}_{product_dict['sku']}")

                LOGGER.debug(f"Index requested for {doc_id}")

                # keep track of updates
                # will be usefull for the frontend to highlight "new" properties scraped
                existing_doc = ElasticCommand.get(zone, doc_id)
                LOGGER.debug(f"Document Existing {doc_id} : {existing_doc}")

                today = datetime.today().strftime('%Y-%m-%d')

                if existing_doc is not None:
                    product_dict['is_new'] = False
                    # update the scraping_end_date
                    # the scraping_start_date remains unchanged
                    product_dict['scraping_end_date'] = today
                else:
                    product_dict['is_new'] = True
                    # Initiate the dates
                    product_dict['scraping_start_date'] = today
                    # at thee beginning, the scraping_end_date is the scraping_start_date
                    product_dict['scraping_end_date'] = today

                ElasticCommand.save(zone, doc_id, product_dict, force_refresh=config.ENV.FORCE_REFRESH)

                if product_dict['is_new']:
                    result.increment_created(1)
                else:
                    result.increment_updated(1)

                LOGGER.debug(f"Saved {product_dict['sku']} in zone {zone}")

            except IndexError as ve:
                # some required fields may haven't been provided
                # always check to avoid uncatched exceptions which would
                # cause celery to retry the task
                LOGGER.error(f"Unable to save {product_dict}", exc_info=True)
                result.increment_errors(1)

    except Exception as se:

        # other technical error raised during classification
        # LOGGER.critical(f"Error occured in task {self.request.id}, {se}", exc_info=True)
        LOGGER.critical(f"Error occured in task : {se}", exc_info=True)

    finally:

        return result.values()
