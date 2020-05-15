# -*- coding: utf-8 -*-

from .base_data import ZONE, NAME

VALID_CATALOGS = [{
    'short_name': NAME,
    'long_name' : 'Test Catalog',
    'zone'  : ZONE,
}]

# invalid catalog are just catalogs that are not found in firebase
# for example a catalog not affected to a ZONE
INVALID_CATALOGS = [{
    'short_name'   : 'www.Câïtalogg-!!, _one',
    # zone is missing
}]
