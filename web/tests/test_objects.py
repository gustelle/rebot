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

from objects import Catalog, User, Area

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
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'][0])
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
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'][0])
        cat = Catalog.from_dict(catalog_dataset)

        result = catalog_dataset
        result['id'] = catalog_dataset['short_name']

        assert cat.to_dict() == result


    def test_init_from_dict_missing_keys(self, mocker, dataset):
        """
        A Catalog object can be initialized with a dict
        """
        catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'][0])
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
        u_dict = copy.deepcopy(dataset['users']['valid'][1])
        user = User.from_dict(u_dict)

        assert user.id == u_dict["id"]
        assert user.firstname == u_dict["firstname"]
        assert user.lastname == u_dict["lastname"]
        assert user.deja_vu[ZONE] == u_dict["deja_vu"][ZONE]
        assert user.tbv[ZONE] == u_dict["tbv"][ZONE]
        assert user.filter.include_deja_vu == bool(u_dict["filter"]["include_deja_vu"])
        assert user.filter.city == u_dict["filter"]["city"]
        assert user.filter.max_price == float(u_dict["filter"]["max_price"])


    def test_from_dict_to_list(self, mocker, dataset):
        """fields where value is provided as comma separated list are converted to python lists"""
        u_dict = copy.deepcopy(dataset['users']['valid'][1])
        u_dict['tbv'] =  {'test': '1,2,3'}
        u_dict['deja_vu'] =  {'test': '4,5,6'}
        u_dict['filter']['city'] =  '1,2,3,4'
        user = User.from_dict(u_dict)

        assert user.id == u_dict["id"]
        assert user.firstname == u_dict["firstname"]
        assert user.lastname == u_dict["lastname"]
        assert user.deja_vu["test"] == u_dict['deja_vu']['test'].split(',')
        assert user.tbv["test"] == u_dict['tbv']['test'].split(',')
        assert user.filter.include_deja_vu == bool(u_dict["filter"]["include_deja_vu"])
        assert user.filter.city == u_dict["filter"]["city"].split(',')
        assert user.filter.max_price == float(u_dict["filter"]["max_price"])


@pytest.mark.usefixtures("mocker", "dataset")
class TestAreaObject(object):
    """
    """
    def test_from_dict(self, mocker, dataset):
        c_dict = copy.deepcopy(dataset['areas']['valid'][0])
        area = Area.from_dict(c_dict)

        assert area.name == c_dict["name"]
        assert area.cities == c_dict["cities"]


    def test_init_with_comma_separated_values(self, mocker, dataset):
        c_dict = copy.deepcopy(dataset['areas']['valid'][0])
        c_dict['cities'] = ','.join(c_dict['cities'])
        area = Area.from_dict(c_dict)

        # rollback the changes on the dataset
        c_dict['cities'] = c_dict['cities'].split(',')

        assert area.name == c_dict["name"]
        assert area.cities == c_dict["cities"]
