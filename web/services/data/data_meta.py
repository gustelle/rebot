# -*- coding: utf-8 -*-
import logging

import config

import utils

from objects import Catalog

from ..exceptions import ServiceError
from ..firebase_service import FirebaseService


LOGGER = logging.getLogger("app")


"""This whole stuff manages the CRUD operations for "catalog" objects which are stored in firebase
"""

class CatalogMeta(FirebaseService):
    """
    """

    def __init__(self):
        """
        sets the tenant of the  FirebaseService
        """
        # separate object types clearly
        # because different objects (models, catalogs) could be stored under the root
        _tenant = config.ENV.ROOT_NODE + '/catalogs'

        super(CatalogMeta, self).__init__(tenant=_tenant)


    def get_catalogs(self):
        """
        Returns the list of registered catalogs
        """
        entries = self.all_values()
        catalog_list = []

        # do not return the keys which are internal Firebase stuff
        # just return the raw data
        for _entry in entries:
            if _entry is not None:
                catalog_list.append(Catalog.from_dict(_entry)) # {name": "Mortimer 'Morty' Smith"}

        self.logger.debug(f"Full catalogs list: {entries}")

        # filter eventually the data, depending on args passed
        # if lang is not None and lang:
        #     self.logger.debug(f"Filtering on lang: {lang}")
        #     catalog_list= [x for x in catalog_list if x.lang == lang]
        #
        # if zone is not None and zone:
        #     self.logger.debug(f"Filtering on zone: {zone}")
        #     catalog_list= [x for x in catalog_list if x.zone == zone]

        return catalog_list


    def get_the_catalog(self, short_name):
        """
        Retrieves a catalog by its short_name

        :param short_name: the unique ID of the catalog
        """

        entry = self.get_value(short_name)

        if entry is None:
            return None

        return Catalog.from_dict(entry)


    def register_catalog(self, catalog):
        """
        Registers a new catalog, or overrides an existing one if the short_name already exists

        :param catalog: an instance of a catalog object

        returns True is succesful, False otherwise
        """
        if not isinstance(catalog, Catalog):
            raise TypeError(f"Exepecting an object of type Catalog, found {type(catalog)}")

        if catalog.short_name is None or not catalog.short_name:
            self.logger.warning(f"Registration of catalog rejected, short_name cannot be blank")
            return False

        data = catalog.to_dict()
        self.set_value(catalog.short_name, data)

        self.logger.debug(f"register_catalog {catalog.short_name}: {data}")
        return True


    def unregister_catalog(self, short_name):
        """
        Deletes a catalog entry from Firebase

        :param short_name: the unique ID of the catalog

        :Example:
        >>> unregister_catalog('lmfr')
        True
        """

        if short_name is None or not short_name:
            self.logger.warning(f"Unregistration of catalog rejected, short_name cannot be blank")
            return False

        self.delete_key(short_name)
        return True
