# -*- coding: utf-8 -*-

import copy
import uuid
from datetime import datetime, timedelta

import pytest
from unittest.mock import patch

from tests.data.base_data import ZONE, CATALOG

from jobs.elastic_task import do_index

import config


@pytest.mark.usefixtures("monkeypatch", "mocker", "dataset")
class TestIndexTask(object):
    """
    """

    async def test_no_sku(self, monkeypatch, mocker, dataset):
        """SKU is required to insert data
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])
        del a_product["sku"]

        # wait for the task to complete with .get()
        # result = index_task.delay([a_product], CATALOG, ZONE).get()
        result = do_index([a_product], CATALOG, ZONE)

        assert "errors" in result and result['errors'] == 1


    async def test_no_ZONE(self, monkeypatch, mocker, dataset):
        """ZONE is required to index data
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        result = do_index([a_product, a_product], CATALOG, "")

        # nothing should be indexed, all products should be in error
        assert "errors" in result and result['errors'] == 2


    async def test_created(self, monkeypatch, mocker, dataset):
        """Indexing NEW data
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # suppose the document does not exist
        # get returns None
        mock_get = mocker.patch("search_index.ElasticCommand.get")
        mock_get.return_value = None

        # wait for the task to complete with .get()
        result = do_index([a_product], "", ZONE)

        args, kwargs = mock_save.call_args
        prop = args[2]
        today = datetime.today().strftime('%Y-%m-%d')

        assert prop['is_new'] == True
        # both dates are equal
        assert prop['scraping_start_date'] == today
        assert prop['scraping_end_date'] == today
        assert result == {'created': 1, 'updated':0, 'errors': 0}



    async def test_updated(self, monkeypatch, mocker, dataset):
        """Indexing NEW data
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        # let's suppose the item has been created yesterday
        yesterday = datetime.today() - timedelta(days = 1)
        a_product['scraping_start_date'] = yesterday.strftime('%Y-%m-%d')
        a_product['scraping_end_date'] = yesterday.strftime('%Y-%m-%d')

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # suppose the document exists
        # get returns an object != None
        mock_get = mocker.patch("search_index.ElasticCommand.get")
        mock_get.return_value = {'id': '1'}

        # wait for the task to complete with .get()
        result = do_index([a_product], "", ZONE)

        args, kwargs = mock_save.call_args
        prop = args[2]
        today = datetime.today().strftime('%Y-%m-%d')

        assert prop['is_new'] == False

        # only the scraping_end_date is touched, scraping_start_date is unchanged
        assert prop['scraping_end_date'] == today
        assert prop['scraping_start_date'] == yesterday.strftime('%Y-%m-%d')
        assert result == {'created': 0, 'updated':1, 'errors': 0}


    async def test_no_catalog(self, monkeypatch, mocker, dataset):
        """Indexing data without catalog is OK
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # suppose the document does not exist
        # this is a creation
        mock_get = mocker.patch("search_index.ElasticCommand.get")
        mock_get.return_value = None

        # wait for the task to complete with .get()
        result = do_index([a_product], "", ZONE)

        assert result == {'created': 1, 'updated':0, 'errors': 0}


    async def test_not_a_list(self, monkeypatch, mocker, dataset):
        """The REPs must be passed as a list
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        # wait for the task to complete with .get()
        result = do_index(a_product, CATALOG, ZONE)

        assert result == {'created': 0, 'updated':0, 'errors': 0}


    async def test_features_enrichment(self, monkeypatch, mocker, dataset):
        """"""

        a_product = copy.deepcopy(dataset['products']['valid'][0])

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # mock the FeaturesExtractor to verify its return value is passed to the product
        mock_extractor = mocker.patch("nlp.FeaturesExtractor.extract")
        mock_extractor.return_value = "my_features"

        # wait for the task to complete with .get()
        do_index([a_product], CATALOG, ZONE)

        # assert the object saved is passed the features extracted
        saved_product = mock_save.call_args[0][2]
        assert saved_product['features'] == "my_features"


    async def test_quality_index(self, monkeypatch, mocker, dataset):
        """"""
        a_product = {
            "url": "",
            "city": "",
            "title": "Maison 3 pièces Houplines",
            "description": "EXCLUSIVITE ! A deux pas du centre ville et des commerces de proximité, le Cabinet GLV Immobilier vous propose cette maison lumineuse des années 30. Elle se compose d'un vaste salon séjour  ouvert sur la cuisine équipée.L'étage vous offre 2 chambres et une salle de douche. Vous profiterez également d'un extérieur bien exposé. Idéale première acquisition ou investissement locatif ! Pour visiter, contacter Marielle Demon Agent Commercial SIREN 839582657 RSAC 2018AC00099 au 07.72.25.69.25.",
            "media": [
              "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_0.jpg",
              "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_1.jpg",
              "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_2.jpg",
              "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_3.jpg",
              "http://www.glv-immobilier.fr/annonce/vente-maison-3-pieces-houplines-9502md_4.jpg"
            ],
            "sku": "9502MD",
            "price": 95000.0,
            "catalog": "glv",
            "area": 90
        }

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # mock the FeaturesExtractor to verify its return value is passed to the product
        mock_extractor = mocker.patch("nlp.FeaturesExtractor.extract")
        mock_extractor.return_value = ["my_features"]

        # wait for the task to complete with .get()
        do_index([a_product], CATALOG, ZONE)

        # expected QI :
        QI = 0
        QI += 1 # title
        QI += 1 # description
        QI += 2 # area is completed
        QI += 2 # media >= 3
        QI += 2 # 1 feature existing ['my_features']

        # assert the object saved is passed the features extracted
        saved_product = mock_save.call_args[0][2]
        assert saved_product['quality_index'] == QI


    @pytest.mark.skip
    async def test_city_sanitization(self, monkeypatch, mocker, dataset):
        """This test is obsolete, city sanitization has been removed
        """
        a_product = copy.deepcopy(dataset['products']['valid'][0])
        a_product['city'] = ';a bad,      -- city! #1'

        # mock everything we can, we just need to verify the features are enriched
        # mock_get = mocker.patch("services.data.data_provider.ProductService.get")
        # mock_get.return_value = False
        # return False to avoid evaluation of 'exists.sku' which would require mocking an elastic object...

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # mock the FeaturesExtractor to verify its return value is passed to the product
        mock_extractor = mocker.patch("nlp.FeaturesExtractor.extract")
        mock_extractor.return_value = "my_features"

        # wait for the task to complete with .get()
        do_index([a_product], CATALOG, ZONE)

        # assert the object saved is passed the features extracted
        saved_product = mock_save.call_args[0][2]
        assert saved_product['city'] == "a bad city 1"


    async def test_create(self, monkeypatch, mocker, dataset):
        """"""
        a_product = copy.deepcopy(dataset['products']['valid'][0])

        # this product does not exist
        # its sku is random generated
        b_product = copy.deepcopy(a_product)
        b_product['sku'] = str(uuid.uuid4())

        mock_save = mocker.patch("search_index.ElasticCommand.save")
        mock_save.return_value = True

        # mock the FeaturesExtractor to verify its return value is passed to the product
        mock_extractor = mocker.patch("nlp.FeaturesExtractor.extract")
        mock_extractor.return_value = "my_features"

        # wait for the task to complete with .get()
        do_index([b_product], CATALOG, ZONE)

        # assert the object saved is passed the features extracted
        saved_product = mock_save.call_args[0][2]
        assert saved_product['sku'] == b_product['sku']
