
import copy
import pytest
import uuid

from objects import Area

from services.area_service import AreaService
from services.exceptions import ServiceError

from tests.data.base_data import ZONE

async def test_get_area(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """"""

    ds = copy.deepcopy(dataset['areas']['valid'][1])

    # create an ad-hox area
    uid = str(uuid.uuid4())
    ds['name'] = uid
    pyrebase_db.child(firebase_root_node + f"/areas/{ZONE}").child(uid).set(ds)

    an_area = Area.from_dict(ds)
    # fetch area to check if it exists !!
    a_service = AreaService(ZONE)
    area = a_service.get_the_area(uid)

    assert isinstance(area, Area)
    assert area.name == ds['name']
    assert area.cities == ds['cities']

    #tear down
    pyrebase_db.child(firebase_root_node + f"/areas/{ZONE}").child(uid).remove()


async def test_save_area_raise_error(test_cli, mocker, dataset):
    """if the user is not of type User"""
    obj = dict()
    with pytest.raises(ServiceError):
        a_service = AreaService(ZONE)
        a_service.register_area(obj)


async def test_register_area(test_cli, mocker, dataset, pyrebase_db, firebase_root_node):
    """"""
    obj = {
        "name": "a",
        "cities": [str(uuid.uuid4()), str(uuid.uuid4())]
    }
    a_area = Area.from_dict(obj)
    a_service = AreaService(ZONE)
    area = a_service.register_area(a_area)

    assert isinstance(area, Area)
    assert area.name == obj["name"]
    assert all(item in obj["cities"] for item in area.cities)
    assert all(item in area.cities for item in obj["cities"])

    #tear down
    pyrebase_db.child(firebase_root_node + f"/areas/{ZONE}").child(obj["name"]).remove()


async def test_get_areas(test_cli, mocker, dataset):
    """"""
    ds = copy.deepcopy(dataset['areas']['valid'])
    a_service = AreaService(ZONE)
    all_areas = a_service.get_areas()

    # print([a.to_dict() for a in all_areas])
    # print("---------------------------")
    # print(ds)

    assert all(isinstance(p, Area) for p in all_areas)
    assert all(item.to_dict() in ds for item in all_areas)
    assert all(item in [a.to_dict() for a in all_areas] for item in ds)
