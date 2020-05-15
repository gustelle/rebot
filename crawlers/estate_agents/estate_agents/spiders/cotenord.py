# -*- coding: utf-8 -*-

import sys
import re
import logging

import scrapy
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for GLV Immobilier"""

    standard_fields = {
        "city": "//h2[@class='titre']/text()",
        "title": "//p[@class='soustitre']/text()",
        "description": "//article[@class='description']//text()",
    }

    special_fields = {
        "media": "//ul[@class='slides']//img/@src",  # prefixer avec 'http://cotenordimmo.com/site/'
        "sku": "//p[@class='ref']/text()",  # extacts - Réf. 2205MD
        "price": "//p[@class='prix']/text()",  # outputs 139 000€ --> format 139000
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        self.logger.info(f"Parsing {resp.request.url}")
        loader = ItemLoader(item=EstateProperty(), response=resp)
        loader.add_value("url", resp.request.url)

        # for the standard fields, extraction is straight forward
        for field, xpath in list(self.standard_fields.items()):
            loader.add_xpath(field, xpath)

        # media url are not complete
        media_dirty = resp.xpath(self.special_fields['media']).extract()
        media = []
        for _pic in media_dirty:
            media.append(f"http://cotenordimmo.com/site/{_pic}")
        loader.add_value('media', media)

        # sku is dirty, starting with "Réf. "
        sku_dirty = resp.xpath(self.special_fields['sku']).extract_first()
        m = re.search(r'.+\:\s(?P<ref>.+)', sku_dirty)
        loader.add_value('sku', m.group('ref'))

        # extract the price
        price_dirty = resp.xpath(self.special_fields['price']).extract_first()
        try:
            m = re.search(r'(?P<price>\d{1,}\s\d{1,}).*', price_dirty)
            float_price = float(m.group('price').replace(" ", ""))
            loader.add_value('price', float_price)
        except TypeError as e:
            self.logger.error(e)
            # mark the item as dirty
            # to avoid sending it
            loader.add_value('is_dirty', True)
        except ValueError as e:
            self.logger.error(e)
            # mark the item as dirty
            # to avoid sending it
            loader.add_value('is_dirty', True)

        yield loader.load_item()


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'cn'
    base_url = f"http://cotenordimmo.com/site/produits.php?type=M"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        links = r.xpath("//a[@class='produit']/@href").extract()
        if links:
            for product_sheet_link in links:
                next_page = r.urljoin(f"http://cotenordimmo.com/site/{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)
