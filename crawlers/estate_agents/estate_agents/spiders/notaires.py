# -*- coding: utf-8 -*-

import sys
import re
import logging
import ujson as json

import scrapy
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup

from ..items import EstateProperty


class BaseSpider(scrapy.Spider):
    """The spider for Notaires Immobilier"""


class HousesForSaleSpider(BaseSpider):
    """
    """
    name = 'notaires'

    def start_requests(self):
       return [ Request(
        url = "https://www.immobilier.notaires.fr/pub-services/inotr-www-annonces/v1/annonces?localites=25323&localites=25455&localites=24975&localites=24827&localites=24953&localites=25080&localites=25400&offset=0&page=1&parPage=12&perimetre=0&typeBiens=MAI&typeTransactions=VENTE&typeTransactions=VNI&typeTransactions=VAE",
        headers={
            'referer': "https://www.immobilier.notaires.fr/fr/annonces-immobilieres-liste?typeBien=MAI&typeTransaction=VENTE,VNI,VAE&localiteGlobale=6679&localite=25323,25455,24975&page=1&parPage=12",
            'Content-Type': 'application/json'
            }
        )]

    def parse(self, r):
        """
        traverse all items of the site map page, and jump to each universe
        """
        # parse JSON response
        products = json.loads(r.body)
        for item in products['annonceResumeDto']:
            loader = ItemLoader(item=EstateProperty())
            loader.add_value("url", item['urlDetailAnnonceFr'])
            loader.add_value("city", item['localiteNom'])
            loader.add_value("title", item['descriptionFr'][:10])
            loader.add_value("description", item['descriptionFr'])
            loader.add_value("media", [item['urlPhotoPrincipale']])
            loader.add_value("sku", str(item['annonceId']))
            loader.add_value("price", str(item['prixTotal']))
            self.logger.debug(f"Loading ended {loader}")
            yield loader.load_item()
