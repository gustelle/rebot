# -*- coding: utf-8 -*-

import pytest

import pyrebase

import ujson as json

from services import firebase_service
from services.cache import *

import config


async def test_get_value_no_cache(pyrebase_db):
    """
    initialize properly the cache to make it work
    """

    tenant = 'test_cache'
    key = 'key'
    value = 'value'

    service = firebase_service.FirebaseService(tenant=tenant)
    service.set_value(key, value)

    # expected value is 'value'.
    intial_value = service.get_value(key)

    # update the firebase entry
    # without passing through 'set_value' which would invalidate the cache
    # otherwise the test could not work
    firebase = pyrebase.initialize_app(config.ENV.FIREBASE_CONFIG)
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(
        config.ENV.FIREBASE_AUTH.get('login'),
        config.ENV.FIREBASE_AUTH.get('password')
    )
    db = firebase.database()
    db.child(tenant).child(key).set('updated_value')

    # the non-cached value
    updated_value = service.get_value(key, use_cache=False)

    # normally, the cached value doesn't change
    cached_value = service.get_value(key, use_cache=True)

    assert intial_value == value == cached_value
    assert updated_value == 'updated_value'

    # tear down
    pyrebase_db.child(tenant).remove()


async def test_set_value(pyrebase_db):
    """
    """
    service = firebase_service.FirebaseService(tenant='test_cache')

    service.set_value('cached_key', 'cached_value')

    # check it has been created
    found = service.get_value('cached_key')

    assert found == 'cached_value'

    # tear down
    pyrebase_db.child("test_cache").remove()


async def test_delete_value(pyrebase_db):
    """
    """
    service = firebase_service.FirebaseService(tenant='test_cache')

    service.set_value('cached_key', 'cached_value')
    service.delete_key('cached_key')

    found = service.get_value('cached_key')

    assert found == None

    # tear down
    pyrebase_db.child("test_cache").remove()


async def test_all_values(monkeypatch, pyrebase_db):
    """
    """
    service = firebase_service.FirebaseService(tenant='test_cache')

    service.set_value('key_one', 'value_one')
    service.set_value('key_two', 'value_two')

    values = service.all_values()

    assert values == ['value_one', 'value_two']

    # tear down
    pyrebase_db.child("test_cache").remove()


async def test_same_tenant_share_cache(mocker, pyrebase_db):
    """
    """
    first_service = firebase_service.FirebaseService(tenant='test_cache')

    other_service = firebase_service.FirebaseService(tenant='test_cache') # same tenant = same cache

    first_service.set_value('cached_key', 'cached_value')

    # check the cache works, the get_value mock should be called once only
    first_call = first_service.get_value('cached_key')
    second_call = other_service.get_value('cached_key')

    assert first_service._cache_info()['currsize'] == 1

    # tear down
    pyrebase_db.child("test_cache").remove()


async def test_per_tenant_cache(monkeypatch, pyrebase_db):
    """
    """
    service_tenant_a = firebase_service.FirebaseService(tenant='test_cache_a')
    service_tenant_b = firebase_service.FirebaseService(tenant='test_cache_b') # different tenants = different caches

    service_tenant_a.set_value('key_one', 'value_one')
    service_tenant_b.set_value('key_two', 'value_two')

    first_call = service_tenant_a.get_value('key_one')
    second_call = service_tenant_a.get_value('key_one')

    # cache_info expect 1 value cached
    assert service_tenant_a._cache_info()['currsize'] == 1

    first_call = service_tenant_b.get_value('key_two')
    second_call = service_tenant_b.get_value('key_two')

    # cache_info expect 1 value cached
    assert service_tenant_b._cache_info()['currsize'] == 1

    # will trigger a clear cache for tenant_a
    service_tenant_a.set_value('key_one', 'value_one')

    # expect cache cleared for tenant a
    assert service_tenant_a._cache_info()['currsize'] == 0
    # but not cleared for the other tenants
    assert service_tenant_b._cache_info()['currsize'] == 1

    # tear down
    service_tenant_a.delete_key('key_one')
    service_tenant_b.delete_key('key_two')

    # delete data used by this test
    pyrebase_db.child("test_cache_a").remove()
    pyrebase_db.child("test_cache_b").remove()
