import sys
import re
import logging

import scrapy
from scrapy.loader import ItemLoader

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for Renoult Habitat Immobilier"""

    standard_fields = {
        "title": "//h3/text()",
        "description": "//div[@class='property_description']/p/text()",
        "media": "//ul[@class='slides']/li/a/@href",
        "price": "//span[@itemprop='price']/@content"
    }

    special_fields = {
        "city": "//h2/a/text()",  # Lys Lez Lannoy : Maison en Vente
        "sku": "//h3/following-sibling::span/a/text()",  # extacts Réf. xxxx
        "price": "//h3/following-sibling::span/following-sibling::span/text()",  # outputs 139 000€ --> format 139000
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

        # city is embedded into a sentence
        city_dirty = resp.xpath(self.special_fields['city']).extract_first()
        loader.add_value('city', city_dirty.split(":")[0])

        # sku is dirty, starting with "Réf. "
        sku_dirty = resp.xpath(self.special_fields['sku']).extract_first()
        m = re.search(r'(?P<ref>\d{1,})', sku_dirty)
        if m:
            loader.add_value('sku', m.group('ref'))

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
    name = 'rh'
    base_url = "http://www.renoult-habitat.com/fr/immobilier/liste-biens.php?transaction=vente&type=1"
    start_urls = [base_url]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        links = r.xpath("//div[@class='property_info_preview']/following-sibling::a/@href").extract()
        if links:
            for product_sheet_link in links:
                next_page = r.urljoin(f"http://www.renoult-habitat.com{product_sheet_link}")
                yield scrapy.Request(next_page, callback=self.parse_product)

            # go to next page
            next_page = r.xpath("(//div[contains(@class, 'pagination')][1]/ul/li)[last()]/a/@href").extract_first()
            self.logger.info(f"Next page : {next_page}")
            yield scrapy.Request(f"http://www.renoult-habitat.com{next_page}")
