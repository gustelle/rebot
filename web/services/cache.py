# -*- coding: utf-8 -*-

import logging

from datetime import datetime, timedelta
from queue import Queue
from threading import Lock

from cachetools import LRUCache
from requests.exceptions import ConnectionError

import inject
import pyrebase

import config

logger = logging.getLogger('app')

"""
This whole stuff enables to avoid solicitating the backend repositories, in particular
firebase which is sensitive to the number of connections

managing a cache enables to reuse connections which better in terms of performance
instead of closing firebase connections / re-opening new ones each time we need to access data
"""

class Proxy:
    """Wraps original object with context manager that return the object to the pool."""
    def __init__(self, obj, pool):
        self._obj = obj
        self._pool = pool

    def __enter__(self):
        return self._obj

    def __exit__(self, typ, val, tb):
        self._pool._put(self._obj)


class Pool:
    """Base abstraction for Pool of objects"""
    def __init__(self, objects):
        self._queue = Queue()
        for obj in objects:
            self._queue.put(obj)

    def lease(self):
        """Lease an object from the pool, should be used as context manger. e.g.:
            with pool.lease() as conn:
                cur = conn.cursor()
                cur.execute('SELECT ...')
        """
        return Proxy(self._queue.get(), self)

    def _put(self, obj):
        self._queue.put(obj)



class Cache(LRUCache):
    """Mask the LRUCache implementation
    to facilate changes
    """


class SimpleCacheProvider():
    """Provides a cache for models
    """
    def __init__(self):
        self.models = Cache(maxsize=1)  # do not cache too many models, they are heavy
        self.logger = logging.getLogger('app')


class TenantCacheProvider():
    """Provides a cache per tenant, a tenant being a way to separate data
    For instance, let's imagine 2 customers A & B sharing the same firebase database,
    the TenantCacheProvider provides a way to isolate the data

    """
    def __init__(self):
        self.tenants_cache = {}
        self.logger = logging.getLogger('app')


    def get_cache(self, tenant):
        """gets / sets the cache for the tenant if not set
        """
        if tenant not in self.tenants_cache:
            self.tenants_cache[tenant] = Cache(maxsize=16)
            self.logger.debug(f"Set a Cache for tenant '{tenant}'")
        else:
            self.logger.debug(f"Reusing Cache for tenant '{tenant}'")

        return self.tenants_cache.get(tenant)


class FirebaseConnection():
    """A firebase connection to be cached in the pool to be reused
    """

    def __init__(self, id=None):
        """
        param   id: optional connection id, useful to identify a connection in a pool for instance. Can be set arbitrarely
        """

        if not id:
            id = ""

        self.logger = logging.getLogger('app')
        self.created = datetime.now()

        # instance of db
        try:
            firebase = pyrebase.initialize_app(config.ENV.FIREBASE_CONFIG)

            self.auth = firebase.auth()
            self.user = self.auth.sign_in_with_email_and_password(
                config.ENV.FIREBASE_AUTH.get('login'),
                config.ENV.FIREBASE_AUTH.get('password')
            )
            self.db = firebase.database()
            self._token = self.user['idToken']
            self.id = f"firebase_{id}"

        except ConnectionError as ce:
            self.logger.critical(f"Unable to open a connection to firebase with config: {config.ENV.FIREBASE_CONFIG}", exc_info=True)
            self.db = None
            self._token = None
            self.id = f"firebase_{id}"


    @property
    def token(self):
        """Firebase tokens make an open connection become obsolete
        thus we need to refresh it from time to time when using a cache of connections
        """
        now  = datetime.now()
        elapsed = now - self.created
        time_difference_in_seconds = elapsed.total_seconds()

        if time_difference_in_seconds > config.ENV.FIREBASE_TOKEN_TIMEOUT:
            self.created = datetime.now()  # refresh the created date otherwise token will be refreshed forever
            self.user = self.auth.refresh(self.user['refreshToken'])
            self._token = self.user['idToken']
            self.logger.info(f"Firebase token for '{self.id}' refreshed")

        return self._token


# dependencies injection
# configure only once, this module may be imported several times
inject.configure_once(lambda binder: binder\
        .bind('simple_cache', SimpleCacheProvider())
        .bind('tenant_cache', TenantCacheProvider())
        .bind('lock', Lock())
        .bind('pool', Pool([FirebaseConnection(id=i) for i in range(config.ENV.FIREBASE_POOL)]))
    )

logger.debug(f"Firebase Pool initiated")
