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
        "city": "//h1/span[@class='uppercase']/text()",
        "title": "//h2[@class='infos_title']/text()",
        "description": "//span[@class='infos_text']/text()",
        "media": "//a[contains(@class, 'fancybox')]/@href",
    }

    special_fields = {
        "sku": "//h1/span[contains(@class, 'ref')]/text()",  # extacts - Réf. 2205MD
        "price": "(//span[@class='price']/text())[1]",  # outputs 139 000€ --> format 139000
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

        # sku is dirty, starting with "Réf. "
        sku_dirty = resp.xpath(self.special_fields['sku']).extract_first()
        m = re.search(r'(?P<ref>\d{1,4}\D{2})', sku_dirty)
        if m:
            loader.add_value('sku', m.group('ref'))
        else:
            loader.add_value("sku", resp.request.url)

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
    name = 'glv'
    page = 1
    base_url = f"http://www.glv-immobilier.fr/scrolling-annonces/?type%5B%5D=maison&transaction=vente"
    start_urls = [base_url + f"&page={page}"]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        raw_html = r.text
        selector = Selector(text=raw_html.replace("\\\"","").replace("\/","/"))
        links = selector.xpath("//div[contains(@class, 'property_container')]//a/@href").extract()
        if links:
            for product_sheet_link in links:
                next_page = r.urljoin(product_sheet_link)
                yield scrapy.Request(next_page, callback=self.parse_product)
            self.page += 1
            self.logger.info(f"Scraping page {self.page}")
            yield scrapy.Request(self.base_url + f"&page={self.page}")
