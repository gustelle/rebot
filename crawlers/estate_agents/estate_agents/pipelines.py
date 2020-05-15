# -*- coding: utf-8 -*-

import sys
import os, collections
import logging
import ujson as json
import requests
import datetime

from .items import ESTATE_PROPERTY_SCHEMA, EstateProperty
from scrapy.exceptions import DropItem

from jsonschema import validate
from jsonschema.exceptions import ValidationError


pipelineLogger = logging.getLogger(__name__)


class HttpPipeline(object):
    """
    comminicates the item per HTTP to the URL set in config.ENV.CLIENT_ON_ADD_ITEM, sending in payload:
    - 'name' : the endpoint name
    - 'zone' : a geographical zone to which scraped items belong (ex: paris_8)
    - 'item' : the item scrapped
    """
    def process_item(self, item, spider):
        """
        """
        ON_PROCESS_ITEM = spider.settings.get('ON_PROCESS_ITEM', None)
        ZONE = spider.settings.get('ZONE', '')
        CATALOG =  spider.name

        if ON_PROCESS_ITEM is not None:
            headers = {'Content-Type': 'application/json'}
            try:
                item = dict(item)

                # do not send for some reasons
                if "is_dirty" in item and bool(item["is_dirty"]):
                    if bool(spider.settings.get('SKIP_DIRTY_ITEMS', False)):
                        raise ValueError(f"Skipping dirty item {item}")

                r = requests.post(ON_PROCESS_ITEM,
                                data=json.dumps({
                                    'catalog': CATALOG,
                                    'zone': ZONE,
                                    'item':dict(item)
                                    }),
                                headers=headers)
                pipelineLogger.debug(f"Item {item.get('sku')} sent to {ON_PROCESS_ITEM}")

            except Exception as e:
                pipelineLogger.error(e)
            finally:
                return item
        else:
            pipelineLogger.error('Missing ON_PROCESS_ITEM setting')



class JsonSchemaValidatePipeline(object):
    """
    Validates the Item against a JSON Schema
    """
    def process_item(self, item, spider):
        """
        """
        try:
            if not isinstance(item, EstateProperty):
                raise DropItem('Invalide item type {}'.format(type(item)))

            # validate raises a ValidationError if the item is not compliant
            # with the scheam
            validate(item, ESTATE_PROPERTY_SCHEMA)
            return item
        except ValidationError as e:
            pipelineLogger.error('JsonSchemaValidatePipeline error for {}'.format(item))
            raise DropItem('Invalid Item definition {}'.format(e.message))



class OnClosePipeline(object):
    """
    sending a POST request to config.ENV.CLIENT_ON_CLOSE notifying the end of the crawling process
    """
    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    def close_spider(self, spider):
        ON_SPIDER_CLOSE = spider.settings.get('ON_SPIDER_CLOSE', None)
        if ON_SPIDER_CLOSE is not None:
            pipelineLogger.debug('closing spider {}'.format(self.stats.get_stats()))
            headers = {'Content-Type': 'application/json'}
            requests.post(ON_SPIDER_CLOSE, data=json.dumps({'spider':spider.name, 'stats':self.stats.get_stats()}), headers=headers)
