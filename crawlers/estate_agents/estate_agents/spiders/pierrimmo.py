import sys
import re
import logging

import scrapy
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for Pierrimmo Immobilier"""

    standard_fields = {
        "city": "//div[@class='bien-title']/span/text()",
        "title": "//div[@class='bien-title']/h1/text()",
        "description": "//div[@itemprop='description']/text()",
        "media": "//div[@class='bien-thumb-container']//img/@src",
        "price": "//span[@itemprop='price']/@content"
    }

    special_fields = {
        "sku": "//span[@class='ref']/text()",  # extacts Ref : xxx
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

        # sku is dirty, starting with "Réf. "
        sku_dirty = resp.xpath(self.special_fields['sku']).extract_first()
        m = re.search(r'\S{3}\s{1}:\s{1}(?P<ref>\S{1,})', sku_dirty)
        if m:
            loader.add_value('sku', m.group('ref'))

        yield loader.load_item()


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'pi'
    base_url = "http://www.pierrimmo.com/vente,c2/"
    start_urls = [base_url]
    page = 1

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        self.logger.info(f"Scraping page {self.page}")
        links = r.xpath("//div[@itemtype='http://schema.org/Product']//h2[@itemprop='name']/a/@href").extract()
        if links:
            for product_sheet_link in links:
                self.logger.info(f"Scraping {product_sheet_link}")
                next_page = r.urljoin(product_sheet_link)
                yield scrapy.Request(next_page, callback=self.parse_product)
            # go to next page
            self.page += 1
            yield scrapy.Request(f"{self.base_url}?page={self.page}")
        else:
            self.logger.info(f"-- No more properties to be scraped --")
