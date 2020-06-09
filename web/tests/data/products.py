# -*- coding: utf-8 -*-

import uuid
import random

from .base_data import NAME

VALID_PRODUCTS = [
{
    "url": "http://www.glv-immobilier.fr/detail/2664-vente-maison-3-pieces-houplines-9502md/",
    "city": "houplines",
    "title": "Maison 3 pièces Houplines",
    "description": "EXCLUSIVITE ! A deux pas du centre ville et des commerces de proximité, le Cabinet GLV Immobilier vous propose cette maison lumineuse des années 30. Elle se compose d'un vaste salon séjour  ouvert sur la cuisine équipée.L'étage vous offre 2 chambres et une salle de douche. Vous profiterez également d'un extérieur bien exposé. Idéale première acquisition ou investissement locatif ! Pour visiter, contacter Marielle Demon Agent Commercial SIREN 839582657 RSAC 2018AC00099 au 07.72.25.69.25.",
    "media": [
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_0.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_1.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_2.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_3.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_4.jpg"
    ],
    "sku": str(uuid.uuid4()),
    "price": 95000.0,
    "features": ["garage", "jardin"]
    # "catalog": "glv"
},
{
    "url": "http://www.glv-immobilier.fr/detail/2664-vente-maison-3-pieces-houplines-9502md/",
    "city": "houplines",
    "title": "Maison 3 pièces Houplines",
    "description": "EXCLUSIVITE ! A deux pas du centre ville et des commerces de proximité, le Cabinet GLV Immobilier vous propose cette maison lumineuse des années 30. Elle se compose d'un vaste salon séjour  ouvert sur la cuisine équipée.L'étage vous offre 2 chambres et une salle de douche. Vous profiterez également d'un extérieur bien exposé. Idéale première acquisition ou investissement locatif ! Pour visiter, contacter Marielle Demon Agent Commercial SIREN 839582657 RSAC 2018AC00099 au 07.72.25.69.25.",
    "media": [
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_0.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_1.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_2.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_3.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_4.jpg"
    ],
    "sku": str(uuid.uuid4()),
    "price": 300000.0,
    "features": ["garage", "jardin"]
    # "catalog": "glv"
},
{
    "url": "http://www.glv-immobilier.fr/detail/2664-vente-maison-3-pieces-houplines-9502md/",
    "city": "lille",
    "title": "Maison 3 pièces Houplines",
    "description": "EXCLUSIVITE ! A deux pas du centre ville et des commerces de proximité, le Cabinet GLV Immobilier vous propose cette maison lumineuse des années 30. Elle se compose d'un vaste salon séjour  ouvert sur la cuisine équipée.L'étage vous offre 2 chambres et une salle de douche. Vous profiterez également d'un extérieur bien exposé. Idéale première acquisition ou investissement locatif ! Pour visiter, contacter Marielle Demon Agent Commercial SIREN 839582657 RSAC 2018AC00099 au 07.72.25.69.25.",
    "media": [
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_0.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_1.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_2.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_3.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_4.jpg"
    ],
    "sku": str(uuid.uuid4()),
    "price": 300000.0,
    "features": ["garage", "jardin"]
    # "catalog": "glv"
},
{
    "url": "http://www.glv-immobilier.fr/detail/2664-vente-maison-3-pieces-houplines-9502md/",
    "city": "lille",
    "title": "Maison 3 pièces Houplines",
    "description": "EXCLUSIVITE ! A deux pas du centre ville et des commerces de proximité, le Cabinet GLV Immobilier vous propose cette maison lumineuse des années 30. Elle se compose d'un vaste salon séjour  ouvert sur la cuisine équipée.L'étage vous offre 2 chambres et une salle de douche. Vous profiterez également d'un extérieur bien exposé. Idéale première acquisition ou investissement locatif ! Pour visiter, contacter Marielle Demon Agent Commercial SIREN 839582657 RSAC 2018AC00099 au 07.72.25.69.25.",
    "media": [
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_0.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_1.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_2.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_3.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_4.jpg"
    ],
    "sku": str(uuid.uuid4()),
    "price": 290000.0,
    "features": ["garage", "jardin"]
    # "catalog": "glv"
},
{
    "url": "http://www.glv-immobilier.fr/detail/2664-vente-maison-3-pieces-houplines-9502md/",
    "city": "lille",
    "title": "Maison 3 pièces Houplines",
    "description": "EXCLUSIVITE ! A deux pas du centre ville et des commerces de proximité, le Cabinet GLV Immobilier vous propose cette maison lumineuse des années 30. Elle se compose d'un vaste salon séjour  ouvert sur la cuisine équipée.L'étage vous offre 2 chambres et une salle de douche. Vous profiterez également d'un extérieur bien exposé. Idéale première acquisition ou investissement locatif ! Pour visiter, contacter Marielle Demon Agent Commercial SIREN 839582657 RSAC 2018AC00099 au 07.72.25.69.25.",
    "media": [
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_0.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_1.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_2.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_3.jpg",
      "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_4.jpg"
    ],
    "sku": str(uuid.uuid4()),
    "price": 280000.0,
    "features": ["garage", "jardin"]
    # "catalog": "glv"
},
{
    "url": "http://www.newdealimmobilier.fr/bien/5661-duplex-lille",
    "title": "APPARTEMENT DUPLEX DE CHARME PROCHE LILLE CENTRE",
    "sku": str(uuid.uuid4()),
    "media": [
      "http://www.newdealimmobilier.fr/media/cache/ad_main/ad/3269638-annonces-5661-88916.jpg",
      "http://www.newdealimmobilier.fr/media/cache/ad_main/ad/3269638-annonces-5661-88916.jpg"
    ],
    "city": "lille",
    "price": 260000.0,
    "description": "Sis Boulevard de La Liberté ce superbe appartement de 59 M2 vous accueille avec deux belles chambres, une grande salle de bain et une piéce de vie lumineuse de 32 M2 vous permettant de recevoir aisement vos visiteurs.     Une cave privative, ainsi qu' une place de parking dans la cour intérieure de cet immeuble hausmanien compléte cette propriété ; à découvrir absolument.     ALFRED HIBON  MANDATAIRE  NEWDEAL IMMOBILIER  RSAC No441-480-100  TEL 06.11.17.03.92 \n                                         lire la suite",
    "features": ["3 chambres", "jardin"]
    # "catalog": "ndi",
},
{
    "url": "http://",
    "title": "New Real Estate Property",
    "sku": str(uuid.uuid4()),
    "media": [
      "http://",
    ],
    "city": "anstaing",
    "price": 284000.0,
    "description": "",
    "features": ["garage", "jardin"]
},
{
    "url": "http://",
    "title": "New Real Estate Property 2",
    "sku": str(uuid.uuid4()),
    "media": [
      "http://",
    ],
    "city": "tressin",
    "price": 285000.0,
    "description": "",
    "features": ["garage", "jardin"]
},
{
    "url": "http://",
    "title": "New Real Estate Property 3",
    "sku": str(uuid.uuid4()),
    "media": [
      "http://",
    ],
    "city": "chereng",
    "price": 286000.0,
    "description": "",
    "features": ["garage", "jardin"]
}
]

INVALID_PRODUCTS = [
{
    "url": "http://www.newdealimmobilier.fr/bien/5661-duplex-lille",
    "title": "APPARTEMENT DUPLEX DE CHARME PROCHE LILLE CENTRE",
    "sku": "AH2828D",
    # "media": [
    #   "http://www.newdealimmobilier.fr/media/cache/ad_main/ad/3269638-annonces-5661-88916.jpg",
    #   "http://www.newdealimmobilier.fr/media/cache/ad_main/ad/3269638-annonces-5661-88916.jpg"
    # ],
    # "city": "lille",
    # "price": 260000.0,
    "description": "Sis Boulevard de La Liberté ce superbe appartement de 59 M2 vous accueille avec deux belles chambres, une grande salle de bain et une piéce de vie lumineuse de 32 M2 vous permettant de recevoir aisement vos visiteurs.     Une cave privative, ainsi qu' une place de parking dans la cour intérieure de cet immeuble hausmanien compléte cette propriété ; à découvrir absolument.     ALFRED HIBON  MANDATAIRE  NEWDEAL IMMOBILIER  RSAC No441-480-100  TEL 06.11.17.03.92 \n                                         lire la suite",
    # "catalog": "ndi",
}
]


def get_product_id(product_dict):
    if product_dict is None or not isinstance(product_dict, dict) or "sku" not in product_dict:
        raise ValueError()
    return f"{NAME}_{product_dict['sku']}"


def random_product():
    p_length = len(VALID_PRODUCTS)
    product_index = random.randint(0, p_length-1)
    return VALID_PRODUCTS[product_index]
