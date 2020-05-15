# -*- coding: utf-8 -*-

"""
This module contains tasks which are supposed to run in background,
managed by a redis queue for long time running tasks
"""

import logging
from datetime import datetime
from urllib.parse import urlparse

from rq import Queue, Worker
from rq_scheduler import Scheduler
from redis import Redis

import config

# import settings to auto-configure sentry used in task do_send_to_sentry
import settings


#############################################################################
LOGGER = logging.getLogger("app")

# Tell RQ what Redis connection to use
# urlparse.uses_netloc.append('redis')
url = urlparse(config.Q.REDIS_URL)
redis_conn = Redis(
    host=url.hostname,
    port=url.port,
    db=0,
    password=url.password
)

# high_q has a higher priority
low_q = Queue("low", connection=redis_conn)

"""
Tasks
"""

def cleanup_user(zone, user_id):
    LOGGER.info(f"Triggering a cleanup of the user {user_id} on zone {zone}")
    job = low_q.enqueue('jobs.user_tasks.do_cleanup', zone, user_id)
    return job.id
