# -*- coding: utf-8 -*-

import datetime
import logging
import operator
from functools import wraps

from cachetools import cachedmethod

from .firebase_service import FirebaseService
from .exceptions import ServiceError

from objects import Area

import config
import utils


class AreaService(FirebaseService):

    def __init__(self, zone):
        """
        An area is attached to a zone
        """
        _tenant = config.ENV.ROOT_NODE + '/areas/' + zone

        # separate object types clearly
        super(AreaService, self).__init__(tenant=_tenant)


    def get_the_area(self, name):
        """
        Retrieves an area by its name

        :param name: the unique name of the area
        """
        entry = self.get_value(name, use_cache=False)
        if entry is None:
            self.logger.warning(f"get_area '{name}': no result !")
            return None

        # attach the id to the object
        # to have an self-descripting object
        entry['name'] = name

        c = Area.from_dict(entry)
        self.logger.debug(f"Loaded area: {c.to_dict()}")
        return c


    def get_areas(self):
        """
        Retrieves all areas
        """
        values = self.all_values()
        return [Area.from_dict(entry) for entry in values]


    def register_area(self, area):
        """
        Stores the area within firebase and returns the stored Area as an object
        """

        if not area or type(area)!=Area:
            raise ServiceError(f"area must be of type Area")

        self.logger.debug(f"AreaService.save_area {area.name} : {area.to_dict()}")
        self.set_value(area.name, area.to_dict())

        saved_c = self.get_value(area.name, use_cache=False)
        return Area.from_dict(saved_c)
