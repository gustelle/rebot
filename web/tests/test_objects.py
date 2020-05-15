# -*- coding: utf-8 -*-
import datetime
import asyncio
import os
import operator
import copy
from distutils.util import strtobool

import codecs
import pytest
import time

import ujson as json

from objects import Catalog, User

from tests.data.base_data import ZONE

import config


@pytest.mark.usefixtures("mocker", "dataset")
class TestCatalogObject(object):
    """
    """
    def test_from_dict(self, mocker, dataset):
        """
        A Catalog object can be initialized with a dict
        """
        catalog_dataset = dataset['catalogs']['valid'][0]
        cat = Catalog.from_dict(catalog_dataset)

        assert cat.short_name == catalog_dataset.get('short_name')
        assert cat.long_name == catalog_dataset.get('long_name')
        assert cat.zone == catalog_dataset.get('zone')
        assert cat.id == cat.short_name


    def test_from_dict_mandatory_shortname(self, mocker, dataset):
        """
        short_name is mandatory
        """
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'][0])
        catalog_dataset['short_name'] = ''

        with pytest.raises(ValueError):
            cat = Catalog.from_dict(catalog_dataset)



    def test_to_dict(self, mocker, dataset):
        """
        a dict view on the class instance
        """
        catalog_dataset = dataset['catalogs']['valid'][0]
        cat = Catalog.from_dict(catalog_dataset)

        result = catalog_dataset
        result['id'] = catalog_dataset['short_name']

        assert cat.to_dict() == result


    def test_init_from_dict_missing_keys(self, mocker, dataset):
        """
        A Catalog object can be initialized with a dict
        """
        catalog_dataset = dataset['catalogs']['valid'][0]
        cat = Catalog.from_dict({
            'short_name': catalog_dataset.get('short_name'),
            # missing the other keys
        })

        assert cat.short_name == catalog_dataset.get('short_name')
        assert cat.long_name == ''
        assert cat.zone == ''
        # assert cat.lang == ''
        assert cat.id == cat.short_name


@pytest.mark.usefixtures("mocker", "dataset")
class TestUserObject(object):
    """
    """
    def test_from_dict(self, mocker, dataset):
        u_dict = dataset['users']['valid'][1]
        user = User.from_dict(u_dict)

        assert user.id == u_dict["id"]
        assert user.firstname == u_dict["firstname"]
        assert user.lastname == u_dict["lastname"]
        assert user.deja_vu[ZONE] == u_dict["deja_vu"][ZONE]
        assert user.tbv[ZONE] == u_dict["tbv"][ZONE]
        assert user.filter.include_deja_vu == bool(u_dict["filter"]["include_deja_vu"])
        assert user.filter.city == u_dict["filter"]["city"]
        assert user.filter.max_price == float(u_dict["filter"]["max_price"])
