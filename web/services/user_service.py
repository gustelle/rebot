# -*- coding: utf-8 -*-

import datetime
import logging
import operator
from functools import wraps

from cachetools import cachedmethod

from .firebase_service import FirebaseService
from .exceptions import ServiceError

from objects import User, UserFilter

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

        u = User.from_dict(entry)
        self.logger.debug(f"Loaded user: {u.to_dict()}")
        return u


    def save_user(self, user):
        """
        Saves user with the one provided, if the user already exists, it is overriden
        For partial update of the user, use save_partial

        :param user: a User object
        :return user: a User object
        """
        if not user or type(user)!=User:
            raise ServiceError(f"User must be of type User")

        user_dict = user.to_dict()

        self.set_value(user_dict.get('id'), user_dict)
        return self.get_user(user_dict.get('id'))


    def save_partial(self, id, filter=None, tbv=None, deja_vu=None, firstname=None, lastname=None):
        """
        Updates attributes that are provided
        if user does not exists, creates a new one with partial values provided

        This method is useful to update only the filter while keeping other attributes
        """
        id = str(id)
        if not id or not id.strip():
            raise ValueError(f"invalid id to set UserFilter")

        self.logger.debug(f"Partial update of user {id} for atts {locals()}")

        _user_to_update = self.get_user(id)
        if not _user_to_update:
            # save_user
            if not filter:
                filter_dict = {}
            else:
                filter_dict = filter.to_dict()

            _user_to_update = User.from_dict({
                    'id': id,
                    'tbv': tbv,
                    'deja_vu': deja_vu,
                    'firstname': firstname,
                    'lastname': lastname,
                    'filter': filter_dict
                })
        else:

            args = locals()# gets a dictionary of all local parameters

            # some atts are protected (start with _) because updated through a setter/getter
            # thus be careful to these atts
            user_model_atts = [item[1:] for item in list(_user_to_update.__dict__.keys()) if item.startswith('_')]
            user_model_atts.extend([item for item in list(_user_to_update.__dict__.keys()) if not item.startswith('_')])

            for arg_name in args:
                if arg_name in user_model_atts:
                    if args[arg_name]:
                        self.logger.debug(f"Updating {arg_name} ({args[arg_name]})")
                        setattr(_user_to_update, arg_name, args[arg_name])
                    else:
                        self.logger.debug(f"User {id}: {arg_name} ignored [{args[arg_name]}]")

        self.set_value(id, _user_to_update.to_dict())
        return self.get_user(id)
