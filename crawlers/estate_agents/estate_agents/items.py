# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import logging
import re

from scrapy.item import Item, Field
from scrapy.loader.processors import Join, MapCompose, TakeFirst, Identity, Compose
from w3lib.html import remove_tags


logger = logging.getLogger(__name__)

# "type" : "object" causes validation errors
# in the pipeline, why ?
ESTATE_PROPERTY_SCHEMA = {
    # "type" : "object",
    "properties" : {
        "sku": {"type" : "string"},
        "title"     : { "type" : "string"},
        "description": { "type" : "string"},
        "price"     : { "type" : "number"},
        "city"    : { "type" : "string"},
        "media" : {"type": "array", "items": { "type": "string" }},
        "url" : {"type" : "string"},
        "is_dirty" : {"type" : "string"},
    },
    "required": ["sku", "title", "price", "city", "url", "media"]
}

######## Some Utils #############
#################################

def isfloat(value):
    try:
        float(value)
        return True
    except:
        return False


def isint(value):
    try:
        int(value)
        return True
    except:
        return False


#################################
#        input_processor        #
#################################


def uft8_serializer(value):
    if isinstance(value, str):
        return value.encode('utf-8')
    return value


def strip(value):
    # logger.info('Striping {} --> {}'.format(value, value.strip()))
    return value.strip()


def log_input(value):
    try:
        logger.debug(f'Value received : {uft8_serializer(value)}')
    except:
        pass
    return value


def lowercase(value):
    return value.lower()


def filter_integer(value):
    if value is None:
        return 0
    if isint(value):
        return int(value)
    return 0

def filter_float(value):
    if value is None:
        return 0.0
    if isfloat(value):
        return float(value)
    return 0.0

def true_if_not_null(value):
    if value is None or value.strip()=='':
        return False
    return True

def blank_if_null(value):
    if value is None or value.strip()=='':
        return ''
    return value


#################################
#       output_processor        #
#################################

class TakeFirstAcceptBlank(object):
    """
    Inspired from the TakeFirst processor
    This output processor returns the first item of a list, even if the item is blank
    """
    def __call__(self, values):
        for value in values:
            return value

class CountItems(object):
    """
    output_processor extension which counts the items
    """
    def __call__(self, values):
        return len(values)

#################################
#################################

class EstateProperty(Item):
    """
    """
    sku = Field(
        input_processor=MapCompose(remove_tags, strip, log_input),
        output_processor=TakeFirst()
    )
    title = Field(
        input_processor=MapCompose(remove_tags, strip, log_input),
        output_processor=TakeFirst()
    )
    description = Field(
        input_processor=MapCompose(remove_tags, strip, log_input),
        output_processor=TakeFirstAcceptBlank()
    )
    price = Field(
        input_processor=MapCompose(filter_float, log_input),
        output_processor=TakeFirst()
    )
    media = Field(
        input_processor=MapCompose(log_input),
    )
    url = Field(
        input_processor=MapCompose(log_input),
        output_processor=TakeFirst()
    )
    city = Field(
        input_processor=MapCompose(remove_tags, strip, log_input, lowercase),
        output_processor=TakeFirst()
    )
    is_dirty = Field(
        input_processor=MapCompose(log_input),
        output_processor=TakeFirst()
    )
