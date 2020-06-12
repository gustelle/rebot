import uuid
import random

from .products import VALID_PRODUCTS, get_product_id, random_product
from .areas import random_area

from .base_data import ZONE


VALID_USERS=[
        {"id": str(uuid.uuid4()), "firstname": "John", "lastname": "Doe"},
        {
            "id": str(uuid.uuid4()),
            "firstname": "Jim",
            "lastname": "Pete",
            "deja_vu": {ZONE: list(set([get_product_id(random_product()) for i in range(0, len(VALID_PRODUCTS)-1)]))},
            "tbv": {ZONE: list(set([get_product_id(random_product()) for i in range(0, len(VALID_PRODUCTS)-1)]))},
            "filter": {
                "city": list(set([random_product().get('city') for i in range(0, len(VALID_PRODUCTS)-1)])),
                "max_price": float(290000),
                "include_deja_vu": True,
                "area": random_area()['name']
            }
        }
]

# provide data for an invlid user
# an invalid user is not compliant with the users JSON schema
# for instance here the firstname is not a string
INVALID_USERS = [
    {"id": str(uuid.uuid4()), "firstname": 1, "lastname": "test"}
]


def assert_user_equals(user_a, user_b):
    """I've been struggling comparing these objects, so I wrote my own comparison"""
    assert isinstance(user_a, dict)
    assert isinstance(user_b, dict)

    # mandatory
    assert "id" in user_a and "id" in user_b and user_a["id"] == user_b["id"]
    assert "firstname" in user_a and "firstname" in user_b and user_a["firstname"] == user_b["firstname"]
    assert "lastname" in user_a and "lastname" in user_b and user_a["lastname"] == user_b["lastname"]

    # not mandatory
    if user_a.get("deja_vu"):
        assert user_b.get("deja_vu")
        for zone, values in user_a.get("deja_vu").items():
            assert zone in user_b.get("deja_vu")
            assert sorted(values) == sorted(user_b.get("deja_vu").get(zone))

    if user_a.get("tbv"):
        assert user_b.get("tbv")
        for zone, values in user_a.get("tbv").items():
            assert zone in user_b.get("tbv")
            assert sorted(values) == sorted(user_b.get("tbv").get(zone))


    if user_a.get("filter"):
        assert user_b.get("filter")
        if "city" in user_a.get("filter"):
            assert "city" in user_b.get("filter")
            assert sorted(user_a.get("filter").get("city")) == sorted(user_b.get("filter").get("city"))
        if "max_price" in user_a.get("filter"):
            assert "max_price" in user_b.get("filter")
            assert float(user_a.get("filter").get("max_price")) == float(user_b.get("filter").get("max_price"))
        if "include_deja_vu" in user_a.get("filter"):
            assert "include_deja_vu" in user_b.get("filter")
            assert bool(user_a.get("filter").get("include_deja_vu")) == bool(user_b.get("filter").get("include_deja_vu"))
        if "area" in user_a.get("filter"):
            assert "area" in user_b.get("filter")
            assert user_a.get("filter").get("area") == user_b.get("filter").get("area")
