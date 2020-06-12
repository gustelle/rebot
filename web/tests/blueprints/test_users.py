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
from objects import User, UserFilter

import config

from tests.data.base_data import ZONE, NAME
from tests.data.users import assert_user_equals
from tests.data.products import get_product_id


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

    # djv is a dict
    for key, val in djv.items():
        # val is an array
        v = get_product_id({'sku': str(uuid.uuid4())})
        djv[key].append(v)

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"deja_vu": djv}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    user_test_dict["deja_vu"] = djv

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

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
        tbv[key].append(get_product_id({
            'sku': str(uuid.uuid4())
        }))

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"tbv": tbv}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    user_test_dict["tbv"] = tbv

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

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

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

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
    user_test_dict['filter']['city'].append(get_product_id({
        'sku': str(uuid.uuid4())
    }))

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

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

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)
    user_test_dict['filter']['max_price'] = 0.0

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_max_price(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """max_price update works"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    user_test_dict['filter']['max_price'] = float(user_test_dict['filter']['max_price']+1)

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_filter_area(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """partial udpate of the filter works"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]
    user_test_dict['filter']['area'] = str(uuid.uuid4())

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # update only the field 'deja_vu'
    response = await test_cli.put(
        f"/users/{user_test_dict['id']}?zone={ZONE}",
        data=json.dumps({"filter": user_test_dict['filter']}),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(user_test_dict['id']).set(dataset['users']['valid'][1])


async def test_put_create_user_using_partial(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """user is not found --> created"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_save = mocker.patch("services.user_service.UserService.save_user")

    # generate a random uid to ensure user does not exist
    unique_id = str(uuid.uuid4())
    response = await test_cli.put(
        f"/users/{unique_id}?zone={ZONE}",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(unique_id).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    mock_cleanup.assert_called()
    mock_save.assert_not_called()  # if not called, means save_partial is called

    user_test_dict['id'] = unique_id
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(unique_id).remove()


async def test_put_create_user_full(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """user is not found --> created, pass the arg partial=false"""
    user_test_dict = copy.deepcopy(dataset['users']['valid'])[1]

    mock_cleanup = mocker.patch("tasks.cleanup_user")
    mock_cleanup.return_value = str(uuid.uuid4())

    mock_partial = mocker.patch("services.user_service.UserService.save_partial")

    # generate a random uid to ensure user does not exist
    unique_id = str(uuid.uuid4())
    response = await test_cli.put(
        f"/users/{unique_id}?zone={ZONE}&partial=false",
        data=json.dumps(user_test_dict),
        headers={"content-type": "application/json"}
    )

    # refetch user in firebase
    user_fetched =  pyrebase_db.child(firebase_root_node + "/users").child(unique_id).get().val()
    assert user_fetched

    # convert to object to pass through all the rules of user objects
    # like conversion to array ...
    user_fetched_obj = User.from_dict(user_fetched)

    mock_cleanup.assert_called()
    mock_partial.assert_not_called()  # if not called, means save_partial is called

    user_test_dict['id'] = unique_id
    assert_user_equals(user_test_dict, user_fetched_obj.to_dict())

    # reset data for the rest of the tests
    pyrebase_db.child(firebase_root_node + "/users").child(unique_id).remove()


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
