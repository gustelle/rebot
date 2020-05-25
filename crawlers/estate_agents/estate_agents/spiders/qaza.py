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
        "title": "//h1[@itemprop='name']/text()",
        "description": "//p[@itemprop='description']/text()",
        "price": "//span[@itemprop='price']/@content",
        "media": "//ul[contains(@class,'imageGallery')]//li/@data-src",
        "city": "(//ol[@class='breadcrumb']/li)[2]/a/text()",
    }

    special_fields = {
        "sku": "//li[@itemprop='productID']/text()",  # Détails du bien - Référence : FR386124
        "title_legacy": "//div[@class='bienTitle']/h2/text()",
        "area": "//span[contains(text(), 'Surface habitable')]/following-sibling::span/text()" #145 m2
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        loader = ItemLoader(item=EstateProperty(), response=resp)
        loader.add_value("url", resp.request.url)

        # for the standard fields, extraction is straight forward
        for field, xpath in list(self.standard_fields.items()):
            loader.add_xpath(field, xpath)

        # exclude items where price is blank
        # may correspond to rentals
        price = resp.xpath(self.standard_fields['price']).extract_first()
        if price is None or price.strip()=="":
            # mark the item as dirty
            # to avoid sending it
            loader.add_value('is_dirty', True)

        # some items' titles are stored in a legacy path
        title = resp.xpath(self.standard_fields['title']).extract_first()
        if title is None or title.strip()=="":
            # try another way
            title = resp.xpath(self.special_fields['title_legacy']).extract_first()
            if title is None or title.strip()=="":
                # mark it dirty
                loader.add_value('is_dirty', True)
            else:
                loader.add_value('title', title)

        # sku is preprended by dirty text
        sku_dirty = resp.xpath(self.special_fields['sku']).extract_first()
        try:
            m = re.search(r'\s{0,}\S{3}\s{1,}(?P<ref>.+)\s{0,}', sku_dirty)
            loader.add_value('sku', m.group('ref'))
        except Exception as e:
            self.logger.error(e)
            loader.add_value('is_dirty', True)

        area_dirty = resp.xpath(self.special_fields['area']).extract_first()
        try:
            m = re.search(r'(?P<area>\d+)\sm.+', area_dirty)
            float_area = float(m.group('area'))
            loader.add_value('area', float_area)
        except Exception as e:
            self.logger.error(e)
            # parsing error on area is not a cause of dirty item

        yield loader.load_item()


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'qaza'
    page = 1
    base_url = f"http://qazaimmobilier.la-boite-immo.com/recherche/"
    start_urls = [base_url + f"{page}"]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        blocs = r.xpath("//article[@itemtype='https://schema.org/Product']//a/@href").extract()
        if blocs:
            for product_sheet_link in blocs:
                next_page = r.urljoin(f"http://qazaimmobilier.la-boite-immo.com{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)

            # paginate
            self.page += 1
            yield scrapy.Request(self.base_url + f"{self.page}")
