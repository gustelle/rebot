import sys
import re
import logging

import scrapy
from scrapy.loader import ItemLoader

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for Renoult Habitat Immobilier"""

    standard_fields = {
        "title": "//div[@class='bienTitle']/h2/text()",
        "description": "//p[@itemprop='description']/following-sibling::p",
        "media": "//ul[contains(@class, 'lSGallery')]/li/a/img/@src",
        "price": "(//span[@itemprop='price']/@content)[1]",
        "city": "(//ol[@class='breadcrumb']/li)[2]",
        "sku": "//li[@itemprop='productID']/text()",
        "media": "//ul[contains(@class, 'imageGallery')]//img/@src"
    }

    special_fields = {
        "area": "//span[contains(text(), 'Surface habitable')]/following-sibling::span/text()"
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

        # area is in the title
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
    name = 'rh'
    page_index = 1
    base_url = f"https://www.renoult-habitat.com/a-vendre/{page_index}"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        links = r.xpath("//meta[@itemprop='url']/@content").extract()
        if links:
            for product_sheet_link in links:
                next_page = r.urljoin(f"http://www.renoult-habitat.com{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)

            # go to next page
            # next_page = r.xpath("(//div[contains(@class, 'pagination')][1]/ul/li)[last()]/a/@href").extract_first()
            self.page_index += 1
            self.logger.info(f"Next page : {self.page_index}")
            yield scrapy.Request(f"https://www.renoult-habitat.com/a-vendre/{self.page_index}")
