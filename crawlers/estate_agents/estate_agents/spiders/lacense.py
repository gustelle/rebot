import sys
import re
import logging

import scrapy
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for La Cense Immobilier"""

    standard_fields = {
        "title": "//h1/text()",
        "description": "//h3/text()",
        "sku": "//div[@class='product-ref']/text()", # Ref : CLV54627
        "city": "//h1/text()", # pattern is city - xxx
    }

    special_fields = {
        # "city": "//h1/text()", # pattern is city - xxx
        "media": "//div[contains(@class, 'item-slider')]//img/@src",  # ../xxx
        "price": "(//span[@class='hono_inclus_price']/text())[1]",  # ** 650 000 €
        "area": "//img[@src='../externalisation/gli/agence-de-la-cense/catalog/images/m2.svg']/@alt" # 72 m2
    }

    def parse_product(self, resp):
        """
        This is a product detail page
        """
        loader = ItemLoader(item=EstateProperty(), response=resp)

        # for the standard fields, extraction is straight forward
        for field, xpath in list(self.standard_fields.items()):
            loader.add_xpath(field, xpath)

        loader.add_value('url', resp.request.url)

        # media is dirty
        all_media_dirty = resp.xpath(self.special_fields['media']).extract()
        all_media = []
        for item in all_media_dirty:
            all_media.append(f"https://www.immo-lacense.com/fiches/{item}")
        loader.add_value('media', all_media)

        # price
        price_dirty = resp.xpath(self.special_fields['price']).extract_first()
        try:
            m = re.search(r'(?P<price>\d{1,}).*', price_dirty)
            float_price = float(m.group('price'))*1000
            loader.add_value('price', float_price)
        except Exception as e:
            self.logger.error(e)
            # mark the item as dirty
            # to avoid sending it
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
    name = 'lc'
    base_url = "http://www.immo-lacense.com/type_bien/4-40/a-vendre.html"
    start_urls = [base_url]
    page = 1

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        # articles = r.xpath("//article[@class='bien']")
        # self.logger.info(f"Scraping page {self.page}, {len(articles)} properties")
        links = r.xpath("//div[@class='cell-product']/a/@href").extract()
        for product_sheet_link in links:
            next_page = r.urljoin(f"http://www.immo-lacense.com/type_bien/{product_sheet_link}")
            yield scrapy.Request(next_page, callback=self.parse_product)

        # go to next page
        self.page += 1
        next_page = r.xpath("(//a[@class='page_suivante']/@href)[1]").extract_first()
        yield scrapy.Request(f"http://www.immo-lacense.com/type_bien/{next_page}")
