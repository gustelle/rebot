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
        "title": "//h1[@itemprop='name']//text()",
        "description": "//p[@itemprop='description']/text()",
        "sku": "//span[contains(@class, 'ref')]/following::text()",
        "city": "(//div[@class='tab-content']//tbody/tr[1]/th)[2]",  # strip()
        "price": "//span[@itemprop='price']/@content",  # 299 000 €
    }

    special_fields = {
        "media": "//ul[contains(@class, 'lSGallery')]/li/a/img/@src",  # ajouter le domaine
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        self.logger.debug(f"Parsing {resp.request.url}")

        loader = ItemLoader(item=EstateProperty(), response=resp)
        loader.add_value("url", resp.request.url)

        # for the standard fields, extraction is straight forward
        for field, xpath in list(self.standard_fields.items()):
            loader.add_xpath(field, xpath)


        # media url are not complete
        media_dirty = resp.xpath(self.special_fields['media']).extract()
        media = []
        if media_dirty:
            for _pic in media_dirty:
                media.append(f"http:{_pic}")
                self.logger.debug(f"Extracted media : {_pic}")
        else:
            # fallback to the logo
            # there are lots of properties without media on this web
            media.append("http://www.abrinor.fr/Design/Img/logo-couleur.svg")
        loader.add_value('media', media)



class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'abrinor'
    base_url = "https://www.abrinor.fr/recherche/"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        blocs = r.xpath("//article[@itemtype='https://schema.org/Product']/a/@href").extract()

        for product_sheet_link in blocs:
            next_page = r.urljoin(f"https://www.abrinor.fr{product_sheet_link}")
            yield scrapy.Request(next_page, callback=self.parse_product)

        all_pages = r.xpath("//ul[@class='pagination']/li/a/@href").extract()
        for page in all_pages:
            next_page = r.urljoin(f"https://www.abrinor.fr{page}")
            yield scrapy.Request(next_page)
