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

            # area is in the title
            area_dirty = r.json()['title']
            try:
                m = re.search(r'\D+(?P<area>\d+)m2.+', area_dirty)
                float_area = float(m.group('area'))
                loader.add_value('area', float_area)
            except Exception as e:
                self.logger.error(e)
                # parsing error on area is not a cause of dirty item

            loader.add_value("city", item['village'])
            loader.add_value("description", item['WiDescriptionLong'])
            loader.add_value("media", [item['imagename']])
            loader.add_value("price", str(item['AdvertisedPrice']))

            sku_dirty = item['reference']
            try:
                m = re.search(r'.+\:\s(?P<ref>.+)', sku_dirty)
                loader.add_value('sku', m.group('ref'))
            except Exception as e:
                self.logger.error(e)
                loader.add_value('is_dirty', True)

            yield loader.load_item()
