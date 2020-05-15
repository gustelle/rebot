# -*- coding: utf-8 -*-

import sys
import re
import logging

import scrapy
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup

from ..items import EstateProperty


class TLBaseSpider(scrapy.Spider):
    """The spider for Thierry Langlois Immobilier"""

    standard_fields = {
        "city": "//div[@class='top-infos']//span[@class='ville']",
        "title": "//div[@class='bottom-infos']//h3/text()",
        "description": "//div[@class='bottom-infos']//p[@class='description']/text()",
        "media": "//div[@class='slider-detail']//figure/img/@src",
    }

    special_fields = {
        "sku": "//div[@class='top-infos']//span[@class='ref']/text()",  # extacts Réf.  2500B --> 2500B
        "price": "//div[@class='top-infos']//span[@class='prix']/text()",  # outputs 139 000€ --> format 139000
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        for index, box in enumerate(resp.xpath('//div[@class="relative"]')):
            loader = ItemLoader(item=EstateProperty(), selector=box)

            self.logger.info(f"Scraping product {resp.xpath(self.special_fields['sku']).extract_first()}")

            loader.add_value("url", resp.request.url)

            # for the standard fields, extraction is straight forward
            for field, xpath in list(self.standard_fields.items()):
                loader.add_xpath(field, xpath)

            # sku is dirty, starting with "Réf. "
            sku_dirty = resp.xpath(self.special_fields['sku']).extract_first()
            m = re.search(r'\S{4}\s{1,}(?P<ref>\S{1,})', sku_dirty)
            if m:
                loader.add_value('sku', m.group('ref'))

            # price is diry, like 139 000€
            price_dirty = resp.xpath(self.special_fields['price']).extract_first()
            m = re.search(r'(?P<price>\d{1,}\s?\d{1,})', price_dirty)
            if m:
                try:
                    float_price = float(m.group('price').replace(" ",""))
                    loader.add_value('price', float_price)
                except ValueError as e:
                    self.logger.error(e)
                    # mark the item as dirty
                    # to avoid sending it
                    loader.add_value('is_dirty', True)

            yield loader.load_item()


class HousesForSaleSpider(TLBaseSpider):
    """
    """
    name = 'tl'
    base_url = "http://www.langlois-immobilier.com/listing.php?page=%s"
    page = 1
    start_urls = [base_url % page]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        links = r.xpath("//div[@class='listing-container']//*[@class='relative']/a/@href").extract()
        if links:
            for product_sheet_link in links:
                # urls are not complete, protocol http(s) is missing
                if not product_sheet_link.startswith('http://www.langlois-immobilier.com/'):
                    product_sheet_link = f"http://www.langlois-immobilier.com/{product_sheet_link}"
                next_page = r.urljoin(product_sheet_link)
                yield scrapy.Request(next_page, callback=self.parse_product)
            # go to next page
            self.page += 1
            self.logger.info(f"Scraping page {self.page}")
            yield scrapy.Request(self.base_url % self.page)
        else:
            self.logger.info(f"No more properties to be scraped on page {self.page}")
