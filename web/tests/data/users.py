import uuid
from .base_data import ZONE, NAME

VALID_USERS=[
        {"id": str(uuid.uuid4()), "firstname": "John", "lastname": "Doe"},
        # user id=2 has some deja_vu dans tbv
        {"id": str(uuid.uuid4()), "firstname": "Jim", "lastname": "Pete", "deja_vu": {"test": [f"{NAME}_9502MD",f"{NAME}_AH2828D"]}, "tbv": {"test": [f"{NAME}_1234"]}, "filter": {"city": ["anstaing", "lille"], "max_price": float(290000), "include_deja_vu": True}}
]

# provide data for an invlid user
# an invalid user is not compliant with the users JSON schema
# for instance here the firstname is not a string
INVALID_USERS = [
    {"id": str(uuid.uuid4()), "firstname": 1, "lastname": "test"}
]
