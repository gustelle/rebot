import uuid
import random

from .products import VALID_PRODUCTS

VALID_AREAS = [
        {
            "name": str(uuid.uuid4()),
            "cities": [VALID_PRODUCTS[0]["city"], VALID_PRODUCTS[1]["city"], VALID_PRODUCTS[2]["city"], VALID_PRODUCTS[3]["city"]]
        },
        {
            "name": str(uuid.uuid4()),
            "cities": [str(uuid.uuid4()), str(uuid.uuid4())]
        }
]

# provide data for an invlid user
# an invalid user is not compliant with the users JSON schema
# for instance here the firstname is not a string
INVALID_AREAS = [
    {"name": str(uuid.uuid4())}
]


def random_area():
    p_length = len(VALID_AREAS)
    area_index = random.randint(0, p_length-1)
    return VALID_AREAS[area_index]
