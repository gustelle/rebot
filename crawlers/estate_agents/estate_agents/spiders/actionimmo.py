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
        "title": "(//div[@class='ariane']/a)[last()]/text()",
        "description": "//p[@class='overwrap']/text()",
        "sku": "(//div[@class='property-detail']/div)[1]/span[2]/h5/text()",
        "city": "(//div[@class='property-detail']/div)[3]/span[2]/text()",
        "area": "//span[normalize-space(text())='Surf. totale']/following-sibling::span/text()",
    }

    special_fields = {
        "price": "//div[contains(@class, 'prixbig')]/text()",
        "media": "//ul/li//img/@src",  # prefix with domain
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        loader = ItemLoader(item=EstateProperty(), response=resp)
        loader.add_value("url", resp.request.url)

        # for the standard fields, extraction is straight forward
        for field, xpath in list(self.standard_fields.items()):
            self.logger.info(f"extracting {field} on {xpath}")
            loader.add_xpath(field, xpath)

        # media url are not complete
        media_dirty = resp.xpath(self.special_fields['media']).extract()
        media = []
        for _pic in media_dirty:
            media.append(f"https://www.action.immo{_pic}")
        loader.add_value('media', media)

        # some items have no city !!
        # mark them dirty
        city = resp.xpath(self.standard_fields['city']).extract_first()
        if city is None or city.strip()=="":
            # mark the item as dirty
            # to avoid sending it
            loader.add_value('is_dirty', True)

        # sku is preprended by dirty text
        # extract the price
        price_dirty = resp.xpath(self.special_fields['price']).extract_first()
        try:
            m = re.search(r'(?P<price_1>\d{1,})\s(?P<price_2>\d{1,}).*', price_dirty)
            loader.add_value('price', float(f"{m.group('price_1')}{m.group('price_2')}"))
        except Exception as e:
            # can be AttributeError, TypeError or ValueError
            self.logger.warning(f"Could not parse {price_dirty}, {e.message}")
            # mark the item as dirty
            # to avoid sending it
            loader.add_value('is_dirty', True)

        yield loader.load_item()


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'actionimmo'
    page = 1
    base_url = f"https://www.action.immo/vente-immobilier-villeneuve-d-ascq.asp?Page="
    start_urls = [base_url + f"{page}"]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        blocs = r.xpath("//div[@class='property-grid']//h3/a/@href").extract()
        if blocs:
            for product_sheet_link in blocs:
                next_page = r.urljoin(f"https://www.action.immo{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)

            # paginate
            self.page += 1
            yield scrapy.Request(self.base_url + f"{self.page}")
