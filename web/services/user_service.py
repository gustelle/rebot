# -*- coding: utf-8 -*-

import datetime
import logging
import operator
from functools import wraps

from cachetools import cachedmethod

from .firebase_service import FirebaseService
from .exceptions import ServiceError

from objects import User

import config
import utils


class UserService(FirebaseService):
    """
    """

    def __init__(self):
        """
        sets the tenant of the  FirebaseService
        """
        _tenant = config.ENV.ROOT_NODE + '/users'

        # separate object types clearly
        super(UserService, self).__init__(tenant=_tenant)


    def _to_array(self, value):
        """convert a string to a list"""
        if isinstance(value, str):
            return [e.strip() for e in value.split(',')]
        return value


    def get_user(self, id):
        """
        Retrieves a user by its id

        :param id: the unique ID of the user
        """
        entry = self.get_value(str(id), use_cache=False)
        if entry is None:
            self.logger.warning(f"get_user '{id}': no result !")
            return None

        # attach the id to the object
        # to have an self-descripting object
        entry['id'] = id

        # fields may be interpreted as strings when values are single
        # be careful to return array
        if 'tbv' in entry:
            for zone, value in entry['tbv'].items():
                entry['tbv'][zone] = self._to_array(value)

        if 'deja_vu' in entry:
            for zone, value in entry['deja_vu'].items():
                entry['deja_vu'][zone] = self._to_array(value)

        if 'filter' in entry and 'city' in entry['filter']:
            entry['filter']['city'] = self._to_array(entry['filter']['city'])

        u = User.from_dict(entry)
        self.logger.debug(f"Loaded user: {u.to_dict()}")
        return u


    def save_user(self, user):
        """
        Stores the user within firebase and returns the stored User

        :param user: a User object
        """

        if not user or type(user)!=User:
            raise ServiceError(f"User must be of type User")

        self.logger.debug(f"UserService.save_user {user.id} : {user.to_dict()}")
        self.set_value(user.id, user.to_dict())

        saved_u = self.get_value(str(user.id), use_cache=False)

        # fields may be interpreted as strings when values are single
        # be careful to return arrays
        if 'tbv' in saved_u:
            for zone, value in saved_u['tbv'].items():
                saved_u['tbv'][zone] = self._to_array(value)

        if 'deja_vu' in saved_u:
            for zone, value in saved_u['deja_vu'].items():
                saved_u['deja_vu'][zone] = self._to_array(value)

        if 'filter' in saved_u and 'city' in saved_u['filter']:
            saved_u['filter']['city'] = self._to_array(saved_u['filter']['city'])

        return User.from_dict(saved_u)
