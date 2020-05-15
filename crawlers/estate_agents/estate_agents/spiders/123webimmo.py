# -*- coding: utf-8 -*-

import sys
import re
import logging
import ujson as json
import requests

import scrapy
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for 123 Web Immobilier"""


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = '123web'
    page = 1
    base_url = "https://data.123webimmo.com/data/json_results_list.asp?pt=1&sid=66,65"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        # parse JSON response
        products = json.loads(r.body)
        for item in products:
            loader = ItemLoader(item=EstateProperty())

            r = requests.get(f"https://data.123webimmo.com/data/json_prop_url.asp?pid={item['PropertyID']}")
            loader.add_value("url", r.json()['url'])
            loader.add_value("title", r.json()['title'])

            loader.add_value("city", item['village'])
            loader.add_value("description", item['WiDescriptionLong'])
            loader.add_value("media", [item['imagename']])
            loader.add_value("price", str(item['AdvertisedPrice']))

            sku_dirty = item['reference']
            m = re.search(r'.+\:\s(?P<ref>.+)', sku_dirty)
            loader.add_value('sku', m.group('ref'))

            yield loader.load_item()
