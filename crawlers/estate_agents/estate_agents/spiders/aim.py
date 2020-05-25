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
        "title": "//h1/text()",
        "description": "//div[@class='descriptif']//text()",
        "sku": "//span[@class='ref']/text()",  # extact
    }

    special_fields = {
        "city": "(//div[contains(@class, 'caracteristiques')]//li)[1]/b/text()",  # faire un strip()
        "media": "//div[contains(@class, 'carrousel-item')]//img/@src",  #prefixer avec le domaine
        "price": "//strong[@class='price']/text()",  # outputs 224 500,00 € --> format 139000
        "area": "//i[@class='icon-surface']/parent::span/text()"
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        self.logger.info(f"Parsing {resp.request.url}")

        # do not scrape properties already sold, info are limited and irrelevant
        if not resp.xpath("//div[@class='bloc-vendu']").extract():
            loader = ItemLoader(item=EstateProperty(), response=resp)
            loader.add_value("url", resp.request.url)

            # for the standard fields, extraction is straight forward
            for field, xpath in list(self.standard_fields.items()):
                loader.add_xpath(field, xpath)

            # sku is dirty, starting with "Réf. "
            city_dirty = resp.xpath(self.special_fields['city']).extract_first()
            loader.add_value("city", city_dirty.strip())

            # sku is dirty, starting with "Réf. "
            media_dirty = resp.xpath(self.special_fields['media']).extract_first()
            loader.add_value("media", f"http://www.avenue-immobilier-metropole.fr/{media_dirty}")

            price_dirty = resp.xpath(self.special_fields['price']).extract_first()
            try:
                m = re.search(r'(?P<price>\d{1,}\s\d{1,}).*', price_dirty)
                float_price = float(m.group('price').replace(" ", ""))
                loader.add_value('price', float_price)
            except Exception as e:
                self.logger.error(e)
                # mark the item as dirty
                # to avoid sending it
                loader.add_value('is_dirty', True)

            area_dirty = resp.xpath(self.special_fields['area']).extract_first()
            try:
                m = re.search(r'\D+(?P<area>\d+)\sm.+', area_dirty)
                float_area = float(m.group('area'))
                loader.add_value('area', float_area)
            except Exception as e:
                self.logger.error(e)
                # parsing error on area is not a cause of dirty item

            yield loader.load_item()
        else:
            self.logger.info(f"Item already sold: {resp.request.url} ")


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'aim'
    page = 1
    base_url = "http://www.avenue-immobilier-metropole.fr/ventes/vous-cherchez-a-acheter-un-bien-/?order=0&view=0&transaction=1&type%5B0%5D=1&agence=0"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        self.logger.info(f"r: {r.request.url}")
        links = r.xpath("//article[@class='bien']/div[@class='content']/a/@href").extract()
        if links:
            for product_sheet_link in links:
                next_page = r.urljoin(f"http://www.avenue-immobilier-metropole.fr/{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)
            self.page += 1
            self.logger.info(f"Scraping page {self.page}")
            yield scrapy.Request(self.base_url + f"&page={self.page}")
