# -*- coding: utf-8 -*-

import logging
import operator
import re

from cachetools import cachedmethod

import inject

from .exceptions import ServiceError
from .cache import *

import config
import utils


class FirebaseService():

    # inject the dependency to be used by _get_from_cache
    _cache_provider = inject.attr('tenant_cache')
    _pool = inject.attr('pool')
    _lock = inject.attr('lock')

    def __init__(self, tenant=config.ENV.ROOT_NODE):
        """
        initializes firebase connection and cache
        """
        self.logger = logging.getLogger('app')
        self._cache = self._cache_provider.get_cache(tenant)
        self.tenant = tenant


    def _cache_info(self):
        return {
            'maxsize': self._cache.maxsize,
            'currsize': self._cache.currsize
        }


    def _sanitize_text(self, text):
        """
        remove '.' in text strings, because Firebase keys do not accept dots
        """
        return utils.safe_text(text)



    @cachedmethod(operator.attrgetter('_cache'), lock=operator.attrgetter('_lock'))
    def _get_from_cache(self, entry_key):
        # with self._lock:
        with self._pool.lease() as conn:
            self.db = conn.db
            self.token = conn.token
            entry = self.db.child(self.tenant).child(entry_key).get(token=self.token)  #
            self.logger.debug(f"got uncached value of '{entry_key}' : {entry.val()}")
            return entry


    def all_values(self):
        """
        fetches all the values stored on the tenant
        """
        if self.tenant is None or not self.tenant:
            return ServiceError("Tenant not set")

        with self._pool.lease() as conn:
            self.db = conn.db
            self.token = conn.token
            all_entries = self.db.child(self.tenant).get(token=self.token)
            if all_entries.each() is None:
                return []
            return [entry.val() for entry in all_entries.each()]


    def get_value(self, key, use_cache=True):
        """
        fetches the value of a key on a given tenant, or returns all_values() if no key is passed
        """
        if self.tenant is None or not self.tenant:
            return ServiceError("Tenant not set")

        if use_cache:
            return self._get_from_cache(key).val()
        else:
            with self._pool.lease() as conn:
                self.db = conn.db
                self.token = conn.token
                try:
                    val = self.db.child(self.tenant).child(key).get(token=self.token).val()
                    self.logger.debug(f"Fetched non-cached value for key '{key}': {val}")
                    return val
                except Exception as e:
                    self.logger.error(f"Error fetching value for key {key}", e)


    def set_value(self, key, value):
        """
        stores a key/value entry

        Lists are serialized as comma separated values, event lists stored into dicts
        """
        if self.tenant is None or not self.tenant:
            return ServiceError("Tenant not set")

        if key is None or not key:
            return ServiceError(f"Cannot set {value} with a null key")

        # do not sanitize but make sure key is a string
        # bad experiences in the past...
        key = str(key)

        with self._pool.lease() as conn:
            self.db = conn.db
            self.token = conn.token

            def _stringify(value):
                """
                convert to strings whatever, for instance an array is transformed into a comma separated list of values
                iterate over the keys and convert all python lists into a comma separated list
                """
                if utils.is_list(value):
                    value = ','.join(str(x) for x in sorted(list(set(value))))
                else:
                    if type(value)==str:
                        # try to convert as a list
                        value = value.split(',')
                        value = ','.join(str(x) for x in sorted(list(set(value))))
                    else:
                        value = str(value)
                return value

            def iterative_type_check(d):
                if type(d)==dict:
                    for k,v in d.items():
                        if type(v)==dict:
                            v = iterative_type_check(v)
                        else:
                            d[k] = _stringify(v)

                # may be simple list
                elif utils.is_list(d):
                    return _stringify(d)

                return d

            safe_obj = iterative_type_check(value)

            self.logger.debug(f"Set {safe_obj} (type {type(safe_obj)}) for key {self.tenant}/{key}")

            self.db.child(self.tenant).child(key).set(safe_obj, token=self.token)  #

        # invalidate the cache to refresh it
        # make sure access to cache is synchronized
        with self._lock:
            self._cache.clear()
            self.logger.debug(f"Cleared cache {self._cache}")


    def delete_key(self, key):
        """
        removes the key entry and its value
        """
        if self.tenant is None or not self.tenant:
            return ServiceError("Tenant not set")

        if key is None or not key:
            return ServiceError("Cannot delete a null key")

        # key provided is taken "as-is"
        # key = self._sanitize_text(key)

        with self._pool.lease() as conn:
            self.db = conn.db
            self.token = conn.token
            self.db.child(self.tenant).child(key).remove(token=self.token)  #
            self.logger.debug(f"Removed key {self.tenant}/{key} from Firebase")

        # invalidate the cache to refresh it
        # make sure access to cache is synchronized
        with self._lock:
            self._cache.clear()
            self.logger.debug(f"Cleared cache {self._cache}")
