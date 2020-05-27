# -*- coding: utf-8 -*-
import math
import numbers
from datetime import datetime
import logging

import config
import utils

from services.user_service import UserService
from services.data.data_provider import ProductService

from elasticsearch import ElasticsearchException

# import to import settings to init logging
import settings

LOGGER = logging.getLogger("app")


def do_cleanup(zone, user_id):
    """
    Iterates over all real estate properties of the user 'deja_vu' and 'tbv' fields for the zone and deletes entries which are not found in Elasticsearch
    This process enables to delete obsolete entries from user preferences

    Parameters:
    zone (str): the geographical zone for which to cleanup the real estate properties that may be orphans
    user_id (str): the user id

    Returns:
    dict: A dictionnary containing the ids of the removed orphans for both real estate props "deja_vu" and "to be visited"
    """

    if not str(user_id).strip():
        raise ValueError(f"id must be set")

    if not zone or not str(zone).strip():
        raise ValueError(f"zone must be set")

    u_service = UserService()
    user = u_service.get_user(user_id)

    if not user:
        raise ValueError(f"User {user_id} not found")

    orphans = {
        'deja_vu': [],
        'tbv': []
    }

    if user.deja_vu and user.deja_vu.get(zone):

        product_service = ProductService(zone)
        new_deja_vu = []
        for zone_rep in user.deja_vu.get(zone):
            try:
                result = product_service.get(id=zone_rep)
                if result is None:
                    orphans['deja_vu'].append(zone_rep)
                    user.deja_vu.get(zone).remove(zone_rep)
                else:
                    new_deja_vu.append(zone_rep)
            except ElasticsearchException as e:
                LOGGER.error(f"Error getting {zone_rep}: {e}")
                # rollback
                new_deja_vu.append(zone_rep)

        user.deja_vu[zone] = new_deja_vu

    if user.tbv and user.tbv.get(zone):

        product_service = ProductService(zone)
        new_tbv = []
        for zone_rep in user.tbv.get(zone):
            try:
                result = product_service.get(id=zone_rep)
                if result is None:
                    orphans['tbv'].append(zone_rep)
                    user.tbv.get(zone).remove(zone_rep)
                else:
                    new_tbv.append(zone_rep)
            except ElasticsearchException as e:
                LOGGER.error(f"Error getting {zone_rep}: {e}")
                # rollback
                new_tbv.append(zone_rep)

        user.tbv[zone] = new_tbv

    u_service.save_user(user)
    return orphans
