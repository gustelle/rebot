# -*- coding: utf-8 -*-

import sys
import re
import logging

import scrapy
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from scrapy.http import FormRequest

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for Abrinor"""

    standard_fields = {
        "title": "//td[@itemprop='name']/text()",
        "description": "//div[@itemprop='description']/text()",
        "sku": "//div[@class='tech_detail']//tr[1]/td[@class='r1']/text()",
        "city": "//span[@itemprop='addressLocality']/text()",
        "price": "//td[@itemprop='price']/@content",
        "media": "//img[@class='rsTmb']/@src",
    }

    # special_fields = {
        # "price": "//td[@itemprop='price']/@content",
        # "media": "//img[@class='rsTmb']/@src",  # prefix with domain
    # }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        loader = ItemLoader(item=EstateProperty(), response=resp)
        loader.add_value("url", resp.request.url)

        # for the standard fields, extraction is straight forward
        for field, xpath in list(self.standard_fields.items()):
            loader.add_xpath(field, xpath)

        yield loader.load_item()


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'logenord'
    page = 1
    base_url = f"http://www.immobilier-logenord.fr/recherche?a=1&b%5B%5D=house&c=&f=&e=&do_search=Rechercher"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        blocs = r.xpath("//div[@itemtype='http://schema.org/Offer']/a/@href").extract()
        if blocs:
            for product_sheet_link in blocs:
                next_page = r.urljoin(f"http://www.immobilier-logenord.fr{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)
