
import copy
import pytest
import uuid

from objects import User

from services.user_service import UserService

from tests.data.base_data import ZONE

from services.exceptions import ServiceError


async def test_get_default_values(test_cli, mocker, dataset):
    """fetch of a user which is incomplete, returns a User object with default values"""

    ds = copy.deepcopy(dataset['users']['valid'][0])
    a_user = User.from_dict(ds)
    # fetch user to check if it exists !!
    u_service = UserService()
    user = u_service.get_user(ds.get('id'))

    assert isinstance(user, User)
    assert user.to_dict()['id'] == str(ds['id']) # id is returned as a string
    assert user.to_dict()['deja_vu'] == {}
    assert user.to_dict()['tbv'] == {}
    assert user.to_dict()['filter'] == {
        'city': [],
        'include_deja_vu': False,
        'max_price': 0.0
    }


async def test_get_comma_separated_values(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """comma separated list of values are converted into arrays"""

    ds = copy.deepcopy(dataset['users']['valid'][1])

    # create an ad-hox user
    uid = str(uuid.uuid4())
    ds['id'] = uid
    pyrebase_db.child(firebase_root_node + "/users").child(uid).set(ds)

    a_user = User.from_dict(ds)
    # fetch user to check if it exists !!
    u_service = UserService()
    user = u_service.get_user(uid)

    # cities list is converted
    cities_list = [e.strip() for e in ds.get('filter').get('city')]

    assert isinstance(user, User)
    assert user.deja_vu[ZONE] == ds.get('deja_vu')[ZONE]
    assert user.tbv[ZONE] == ds.get('tbv')[ZONE]
    assert user.filter.city == cities_list

    #tear down
    pyrebase_db.child(firebase_root_node + "/users").child(uid).remove()


async def test_save_user_raise_error(test_cli, mocker, dataset):
    """if the user is not of type User"""
    obj = dict()
    with pytest.raises(ServiceError):
        u_service = UserService()
        u_service.save_user(obj)


async def test_save_user(test_cli, mocker, dataset):
    """"""
    obj = {
        "id": "a",
        "firstname": "b",
        "lastname": "c",
        "deja_vu": {"test": "d, e"},
        "tbv": {"test": "f, g"},
        "filter": {
            "include_deja_vu": "false",
            "city": "h, i",
            "max_price": "1"
        }
    }
    a_user = User.from_dict(obj)

    u_service = UserService()
    user = u_service.save_user(a_user)

    assert user.id == obj["id"]
    assert user.firstname == obj["firstname"]
    assert user.lastname == obj["lastname"]
    assert user.deja_vu == {"test": [e.strip() for e in obj["deja_vu"]["test"].split(',')]}
    assert user.tbv == {"test": [e.strip() for e in obj["tbv"]["test"].split(',')]}
    assert user.filter.include_deja_vu == False
    assert user.filter.city ==  [e.strip() for e in obj["filter"]["city"].split(',')]
    assert user.filter.max_price ==  float(obj["filter"]["max_price"])
