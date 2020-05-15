# -*- coding: utf-8 -*-
import copy
import pytest
import uuid

import pyrebase

import ujson as json

from elasticsearch import ElasticsearchException

from services import firebase_service, elastic_service
from jobs.user_tasks import do_cleanup

from objects import User

from tests.data.base_data import ZONE


async def test_do_cleanup_no_zone():
    """raise ValueError"""
    with pytest.raises(ValueError):
        do_cleanup("", "1")


async def test_do_cleanup_no_user_id():
    """raise ValueError"""
    with pytest.raises(ValueError):
        do_cleanup("zone", "")


async def test_do_cleanup_invalid_user(mocker, dataset):
    """raise ValueError"""
    with pytest.raises(ValueError):
        ds = copy.deepcopy(dataset['users']['invalid'][0])
        do_cleanup(ZONE, ds['id'])


async def test_do_cleanup_no_orphans(mocker, dataset):
    """returns a dict with orphans for deja_vu and tbv, the orphans lists are void"""
    ds = copy.deepcopy(dataset['users']['valid'][1])

    ret_val = do_cleanup(ZONE, ds['id'])

    assert ret_val == {'deja_vu': [], 'tbv': []}


async def test_do_cleanup_with_orphans(mocker, dataset, pyrebase_db, firebase_root_node):
    """returns a dict with orphans for deja_vu and tbv, the orphans are deleted from user preferences in firebase"""
    ds = copy.deepcopy(dataset['users']['valid'][1])

    # simulate orphans on both deja_vu and tbv
    # insert non existing ids in user info in firebase
    orphan = str(uuid.uuid4())
    ds['deja_vu'][ZONE].append(orphan)
    ds['tbv'][ZONE].append(orphan)
    pyrebase_db.child(firebase_root_node + "/users").child(ds['id']).set(ds)

    # mock the user update and assert the arg passed
    mock_save_user = mocker.patch("services.user_service.UserService.save_user")

    ret_val = do_cleanup(ZONE, ds['id'])

    args, kwargs = mock_save_user.call_args

    assert ret_val == {'deja_vu': [orphan], 'tbv': [orphan]}
    assert orphan not in args[0].deja_vu.get(ZONE)
    assert orphan not in args[0].tbv.get(ZONE)


async def test_do_cleanup_elastic_exception(mocker, dataset, pyrebase_db, firebase_root_node):
    """the user deja_vu and tbv remain unchanged"""

    ds = copy.deepcopy(dataset['users']['valid'][1])

    # simulate orphans on both deja_vu and tbv
    # insert non existing ids in user info in firebase
    orphan = str(uuid.uuid4())
    ds['deja_vu'][ZONE].append(orphan)
    ds['tbv'][ZONE].append(orphan)
    pyrebase_db.child(firebase_root_node + "/users").child(ds['id']).set(ds)

    mock_get = mocker.patch("services.data.data_provider.ProductService.get")
    mock_get.side_effet = ElasticsearchException()

    # mock the user update and assert the arg passed
    mock_save_user = mocker.patch("services.user_service.UserService.save_user")

    ret_val = do_cleanup(ZONE, ds['id'])

    args, kwargs = mock_save_user.call_args

    assert ret_val == {'deja_vu': [], 'tbv': []}
    assert orphan in args[0].deja_vu.get(ZONE)
    assert orphan in args[0].tbv.get(ZONE)
