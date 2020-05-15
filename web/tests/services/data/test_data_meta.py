# -*- coding: utf-8 -*-
import copy
import operator

import pytest

import ujson as json

from services.data import data_meta

from objects import Catalog

import config


async def test_registration_of_a_new_catalog(monkeypatch, dataset):
    """
    """
    catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
    catalog_dataset[0]['short_name'] = 'registered_cat'  # do not touch the reference dataset in firebase

    service = data_meta.CatalogMeta()
    the_catalog  = Catalog.from_dict(catalog_dataset[0])
    ret = service.register_catalog(the_catalog)

    # returned value is True
    assert ret

    # check it has been created
    cat_found = service.get_the_catalog('registered_cat')

    assert cat_found.to_dict() == the_catalog.to_dict()


async def test_registration_of_a_catalog_is_not_possible_without_shortname(monkeypatch, dataset):
    """
    The short_name is mandatory in the data structure
    """
    catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])

    service = data_meta.CatalogMeta()

    the_catalog = Catalog.from_dict(catalog_dataset[0])
    the_catalog.short_name = ''

    ret = service.register_catalog(the_catalog)

    # returned value is False
    assert not ret

    # check it has been created
    all_spiders = service.get_catalogs()

    # double check it has not been created in Firebase
    should_not_exist_in_firebase = the_catalog.to_dict()

    # returns the next items which equals 'comparable_spider'
    # or False if not found
    data = next((item for item in all_spiders if operator.eq(item.to_dict(), should_not_exist_in_firebase)), False)

    assert not data


async def test_registration_of_an_existing_catalog_overrides_it(monkeypatch, dataset):
    """
    """
    catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
    catalog_dataset[0]['short_name'] = 'registered_cat'  # do not touch the reference dataset in firebase

    service = data_meta.CatalogMeta()
    the_catalog = Catalog.from_dict(catalog_dataset[0])
    ret = service.register_catalog(the_catalog)

    # returned value is True
    assert ret

    # count the number of items
    all_spiders = service.get_catalogs()
    all_spiders_count = len(all_spiders)

    # register the same spider
    ret = service.register_catalog(the_catalog)

    # returned value is True
    assert ret

    # check the count of spiders  is the smae
    new_all_spiders = service.get_catalogs()
    new_count = len(new_all_spiders)

    # returned value is False
    assert new_count == all_spiders_count


async def test_unregister_a_catalog_works_properly(monkeypatch, dataset):
    """
    """
    catalog_dataset = copy.deepcopy(dataset['catalogs']['valid'])
    catalog_dataset[0]['short_name'] = 'registered_cat'  # do not touch the reference dataset in firebase

    service = data_meta.CatalogMeta()
    the_catalog = Catalog.from_dict(catalog_dataset[0])

    # register the same spider
    ret = service.unregister_catalog(
            the_catalog.short_name
        )

    # fetch the spiders
    all_spiders = service.get_catalogs()

    # returns the next items which equals the_catalog or False if not found
    data = next((item for item in all_spiders if operator.eq(item.to_dict(), the_catalog.to_dict())), False)

    assert not data
