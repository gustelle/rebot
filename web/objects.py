# -*- coding: utf-8 -*-

from distutils.util import strtobool

import datetime
import logging

import utils

LOGGER = logging.getLogger('app')


class DictionaryObject(object):
    """Super class used for serialization
    """

    def to_dict(self):
        """
        provides a dictionary view of the class instance

        :Example:
        >>> o = ContextualizedObject('ctx', value=1, state=State.STARTED)
        >>> o.to_dict()
        {
            'context': 'ctx',
            'value': 1,
            'state': State.STARTED
        }
        """
        all_atts = self.__dict__.keys()

        # do not give the user the view on internal fields
        # like contextualization fields
        # dict_atts = [k for k in all_atts if k not in ['logger'] and not k.startswith('__ctx__')]

        dict_view = {k: getattr(self, k) for k in all_atts}

        # # the context is part of the catalog view
        # dict_view['context'] = self.context

        return dict_view


class Catalog(DictionaryObject):
    """
    Busines object representing a catalog
    """
    def __init__(self, short_name, long_name, zone):

        # short_name is not sanitized
        # suppose the user provides a correct short_name
        self.short_name = short_name

        # long_name is not sanitized
        self.long_name = long_name

        # may be different later
        self.id = self.short_name

        # self.lang = utils.safe_text(lang)
        self.zone = utils.safe_text(zone)


    @classmethod
    def from_dict(cls, dictionary):
        """
        convenience method to load an object with a dictionary

        Missing values for lang, zone and long_name are replaced with ''
        """
        if dictionary.get('short_name') is None or not dictionary.get('short_name'):
            raise ValueError('Unable to initialize object')

        return cls(
            dictionary.get('short_name'),
            dictionary.get('long_name', ''),
            dictionary.get('zone', '')
        )

    def __repr__(self):
        """
        the string representation of the class instance is the id of the catalog
        """
        return f"Catalog <shortname: '{self.id}', zone: '{self.zone}'>"



class UserFilter:
    """Comma separated list of values are converted to arrays"""

    def __init__(self, dictionary):
        """None value is OK"""
        if dictionary and not isinstance(dictionary, dict):
            raise ValueError('Unable to initialize object')

        # converting a string to bool is tricky
        # for example bool("false") == True
        # use strtobool to facilitate casting
        self.include_deja_vu = bool(strtobool(str(dictionary.get('include_deja_vu', False))))

        if dictionary.get('city') is not None and utils.is_list(dictionary.get('city')):
            self.city = dictionary.get('city')
        elif isinstance(dictionary.get('city'), str):
            self.city = [e.strip() for e in dictionary.get('city').split(',')]
        else:
            LOGGER.warning(f"{dictionary.get('city')} is not a valid type for city")
            self.city = []

        self.max_price = float(dictionary.get('max_price', 0))


    def to_dict(self):
        """Overrides the parent method to convert arrays to comma separated values"""

        if self.city is None:
            self.city = []

        return {
            'include_deja_vu': self.include_deja_vu,
            'city': self.city,
            'max_price': self.max_price
        }



class User(DictionaryObject):
    """
    Busines object representing a user
    """


    def __init__(self, id, firstname, lastname, filter):
        """Comma separated list of values are converted to arrays"""

        self.id = str(id)

        self.firstname = firstname
        self.lastname = lastname

        # accessed through properties
        self._deja_vu = {}
        self._tbv = {}

        self.filter = UserFilter(filter)


    @property
    def deja_vu(self):
        """
        Returns:
        dict: a dict of arrays of unique items
        """
        for key, val in self._deja_vu.items():
            if isinstance(val, str):
                self._deja_vu[key] = list(set([e.strip() for e in val.split(',')]))
        return self._deja_vu


    @deja_vu.setter
    def deja_vu(self, value):
        """Accepts both lists and comma separated lists of values, but stores lists"""
        if isinstance(value, dict):
            self._deja_vu = {}
            for zone, props in value.items():
                # remove non lists
                if isinstance(props, str):
                    self._deja_vu[zone] = [e.strip() for e in props.split(',')]
                elif utils.is_list(props):
                    self._deja_vu[zone] = props
                else:
                    LOGGER.warning(f"{props} is not a valid type for deja_vu on zone {zone}")
                    self._deja_vu[zone]= []
        else:
            LOGGER.warning(f"{value} is not a valid type for deja_vu")


    @property
    def tbv(self):
        """
        Returns:
        dict: a dict of arrays of unique items
        """
        for key, val in self._tbv.items():
            if isinstance(val, str):
                self._tbv[key] = list(set([e.strip() for e in val.split(',')]))
        return self._tbv


    @tbv.setter
    def tbv(self, value):
        if isinstance(value, dict):
            self._tbv = {}
            for zone, props in value.items():
                # remove non lists
                if isinstance(props, str):
                    self._tbv[zone] = [e.strip() for e in props.split(',')]
                elif utils.is_list(props):
                    self._tbv[zone] = props
                else:
                    LOGGER.warning(f"{props} is not a valid type for tbv on zone {zone}")
                    self._tbv[zone]= []
        else:
            LOGGER.warning(f"{value} is not a valid type for tbv")


    @classmethod
    def from_dict(cls, dictionary):
        """
        convenience method to load an object with a dictionary

        Missing values for lang, zone and long_name are replaced with ''
        """
        if not dictionary or not isinstance(dictionary, dict):
            raise ValueError('Unable to initialize object')

        if dictionary.get('id') is None or not dictionary.get('id'):
            raise ValueError('Unable to initialize object')

        obj = cls(
            dictionary.get('id'),
            dictionary.get('firstname', ''),
            dictionary.get('lastname', ''),
            dictionary.get('filter', {}),
        )
        obj.deja_vu = dictionary.get('deja_vu', {})
        obj.tbv = dictionary.get('tbv', {})

        return obj



    def to_dict(self):
        """Overrides the parent method to convert arrays to comma separated values"""

        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'deja_vu': self.deja_vu,
            'tbv': self.tbv,
            'filter': self.filter.to_dict()
        }



    def __repr__(self):
        """
        the string representation of the class instance
        """
        return f"User <id: '{self.id}'>"


class Area(DictionaryObject):
    """
    Busines object representing a group of cities
    """


    def __init__(self, name, cities):
        """Comma separated list of values are converted to arrays"""

        self.name = str(name)

        if cities and isinstance(cities, str):
            self.cities = [e.strip() for e in cities.split(',')]
        elif utils.is_list(cities):
            self.cities = cities


    @classmethod
    def from_dict(cls, dictionary):
        """
        convenience method to load an object with a dictionary
        """
        if not dictionary or not isinstance(dictionary, dict):
            raise ValueError('Unable to initialize object')

        if dictionary.get('name') is None or not dictionary.get('name'):
            raise ValueError('Unable to initialize object')

        obj = cls(
            dictionary.get('name'),
            dictionary.get('cities', []),
        )

        return obj


    def to_dict(self):
        """Overrides the parent method to convert arrays to comma separated values"""

        return {
            'name': self.name,
            'cities': self.cities,
        }


    def __repr__(self):
        """
        the string representation of the class instance
        """
        return f"CityArea <name: '{self.name}'>"
