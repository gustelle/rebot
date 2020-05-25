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
    """The spider for New Deal Immobilier"""

    standard_fields = {
        "title": "//h1/text()",
        "sku": "(//div[@class='additional-infos']//strong/text())[1]",  # extact
        "media": "//div[contains(@class, 'picture')]/img/@src",
    }

    special_fields = {
        "city": "(//div[@class='infos']/h2/em)[2]",  # supprimer le code postal
        "price": "//div[contains(@class, 'price')]/text()",  # outputs 224 500 --> format 139000
        "description": "//div[contains(@class,'description')]//text()",  # need to concat the values
        "area": "//i[contains(@class, 'fa-arrows-alt')]/following::em[1]"
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        bloc_vendu = resp.xpath("//span[@class='status-tag']/text()").extract_first()
        if not bloc_vendu or resp.xpath("//span[@class='status-tag']/text()").extract_first()!='VENDU':
            loader = ItemLoader(item=EstateProperty(), response=resp)
            loader.add_value("url", resp.request.url)

            # for the standard fields, extraction is straight forward
            for field, xpath in list(self.standard_fields.items()):
                loader.add_xpath(field, xpath)

            # city is preprended with zipcode, remove it
            city_dirty = resp.xpath(self.special_fields['city']).extract_first()
            try:
                m = re.search(r'(?P<city>.+)\s?\(\d{1,}?\)?', city_dirty)
                loader.add_value('city', m.group('city'))
            except Exception as e:
                self.logger.error(e)
                # mark the item as dirty
                # to avoid sending it
                loader.add_value('is_dirty', True)

            # price contains whitespaces, remove it
            price_dirty = resp.xpath(self.special_fields['price']).extract_first()
            try:
                float_price = float(price_dirty.replace(" ", ""))
                loader.add_value('price', float_price)
            except Exception as e:
                self.logger.error(e)
                # mark the item as dirty
                # to avoid sending it
                loader.add_value('is_dirty', True)

            area_dirty = resp.xpath(self.special_fields['area']).extract_first()
            try:
                loader.add_value('area', float(area_dirty))
            except Exception as e:
                self.logger.error(e)
                # parsing error on area is not a cause of dirty item

            # description : join the paragraphs
            loader.add_value('description', ' '.join(resp.xpath(self.special_fields['description']).extract()))

            yield loader.load_item()
        else:
            self.logger.info(f"Item already sold: {resp.request.url} ")


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'ndi'
    page = 1
    base_url = "http://www.newdealimmobilier.fr/ou-intervenons-nous/immobilier-metropole-lilloise"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        links = r.xpath("//div[@class='title']/a/@href").extract()
        if links:
            for product_sheet_link in links:
                next_page = r.urljoin(f"http://www.newdealimmobilier.fr{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)
            self.page += 1
            self.logger.info(f"Scraping page {self.page}")
            yield scrapy.Request(self.base_url + f"&page={self.page}")
