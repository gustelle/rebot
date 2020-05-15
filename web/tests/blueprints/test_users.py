# -*- coding: utf-8 -*-
import copy
import uuid
import random
import time

import pytest

import ujson as json

from main import app

from services.user_service import UserService
from services.exceptions import ServiceError
from objects import User

import config

from tests.data.base_data import ZONE, NAME


async def test_get(test_cli, mocker, dataset):
    """check user attributes"""
    user_one = copy.deepcopy(dataset['users']['valid'])[1]

    response = await test_cli.get(f"/users/{user_one['id']}")

    jay = await response.json()
    user_fetched =  jay['result']

    assert user_fetched == user_one


async def test_get_non_existing(test_cli, mocker, dataset):
    """returns 404"""
    response = await test_cli.get(f"/users/none")

    assert response.status == 404


async def test_put_id_error(test_cli, mocker, dataset):
    """raise 400"""
    response = await test_cli.put(f"/users/ ")

    assert response.status == 400


async def test_put_no_zone(test_cli, mocker, dataset):
    """returns a 400"""
    response = await test_cli.put(f"/users/1?zone=")

    assert response.status == 400


async def test_put_json_schema_error_deja_vu(test_cli, mocker, dataset):
    """simulate an error in the deja_vu, returns json with error message"""

    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    # deja_vu should be a dict, the key being the zone
    # here 'deja_vu' is passed as an array, which is not valid
    user_test_dict['deja_vu'] = ["1"]

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and not jay['success']


async def test_put_deja_vu(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """partial update of deja_vu --> old info are merged"""

    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    djv = user_test_dict['deja_vu']
    for key, val in djv.items():
        djv[key].append("test")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"deja_vu": djv}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{user_test_dict['id']}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    user_test_dict['deja_vu'] = djv
    assert user_fetched == user_test_dict

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_json_schema_error_tbv(test_cli, mocker, dataset):
    """simulate an error in the tbv, returns json with error message"""

    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    # deja_vu should be a dict, the key being the zone
    # here 'deja_vu' is passed as an array, which is not valid
    user_test_dict['tbv'] = ["1"]

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and not jay['success']


async def test_put_tbv(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """partial update of tbv --> old info are merged"""

    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    tbv = user_test_dict['tbv']
    for key, val in tbv.items():
        tbv[key].append("test")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"tbv": tbv}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{user_test_dict['id']}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    user_test_dict['tbv'] = tbv
    assert user_fetched == user_test_dict

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_json_schema_error_filter_object(test_cli, mocker, dataset):
    """simulate an error in the filter, returns json with error message"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    user_test_dict['filter'] = "yeah"

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and not jay['success']


# async def test_put_filter(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
#     """partial udpate of the filter works"""
#     user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
#
#     # update only the field 'deja_vu'
#     response = await test_cli.put(
#         f"/users/{user_test_dict['id']}?zone={ZONE}",
#         data=json.dumps({"filter": {"key": "val"}}),
#         headers={"content-type": "application/json"}
#     )
#
#     jay = await response.json()
#     assert jay and jay['success']
#
#     # fetch the user and check the info have been updated
#     response_get = await test_cli.get(f"/users/{user_test_dict['id']}")
#
#     jay = await response_get.json()
#     user_fetched =  jay['result']
#
#     user_test_dict['filter'] = {"key", "val"}
#     assert user_fetched == user_test_dict
#
#     # reset data for the rest of the tests
#     pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_json_schema_error_filter_include_deja_vu(test_cli, mocker, dataset):
    """simulate an error in the filter, returns json with error message"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    user_test_dict['filter'] = {"include_deja_vu": "yeah"}

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and not jay['success']


async def test_put_filter_include_deja_vu(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """partial udpate of the filter works"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    user_test_dict['filter']['include_deja_vu'] = not user_test_dict['filter']['include_deja_vu']

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{user_test_dict['id']}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    assert user_fetched == user_test_dict

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_json_schema_error_filter_city(test_cli, mocker, dataset):
    """simulate an error in the filter, returns json with error message"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    user_test_dict['filter'] = {"city": "yeah"}

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and not jay['success']


async def test_put_filter_city(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """partial udpate of the filter works"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    user_test_dict['filter']['city'].append("test")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{user_test_dict['id']}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    assert user_fetched == user_test_dict

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_json_schema_error_max_price(test_cli, mocker, dataset):
    """simulate an error in the filter, returns json with error message"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    user_test_dict['filter'] = {"max_price": "one"}

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and not jay['success']


async def test_put_max_price_negative(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """max_price negative --+> transformed into 0"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    user_test_dict['filter']['max_price'] = float(-1)

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{user_test_dict['id']}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    user_test_dict['filter']['max_price'] = 0.0
    assert user_fetched == user_test_dict

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_max_price(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """max_price update works"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    user_test_dict['filter']['max_price'] = float(user_test_dict['filter']['max_price']+1)

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{user_test_dict['id']}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    assert user_fetched == user_test_dict

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_create_user(test_cli, mocker, dataset):
    """user is not found --> created"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    # generate a random uid to ensure user does not exist
    unique_id = str(uuid.uuid4())
    response = await test_cli.put(
        f"/users/{unique_id}?zone={ZONE}",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    jay = await response.json()
    assert jay and jay['success']

    # fetch the user and check the info have been updated
    response_get = await test_cli.get(f"/users/{unique_id}")

    jay = await response_get.json()
    user_fetched =  jay['result']

    user_test_dict['id'] = unique_id  #.replace("-", "")
    assert user_fetched == user_test_dict


async def test_put_cleanup_user(test_cli, mocker, dataset):
    """a job is triggered to remove obsolete real estates from user prefs"""

    class Job():
        def __init__(self):
            self.id = ""

    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    mock_rq = mocker.patch("rq.Queue.enqueue")
    mock_rq.return_value = Job()

    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    args, kwargs = mock_rq.call_args

    assert args[0] == "jobs.user_tasks.do_cleanup"
    assert args[1] == ZONE
    assert args[2] == user_test_dict['id']
