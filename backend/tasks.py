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

from jobs.elastic_task import do_cleanup


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
high_q = Queue("high", connection=redis_conn)
std_q = Queue("default", connection=redis_conn)
low_q = Queue("low", connection=redis_conn)

"""
Tasks
"""

def index_items(products_list, catalog='', zone=''):
    job = high_q.enqueue('jobs.elastic_task.do_index', products_list, catalog, zone)
    return job.id

def report_error(products_list, catalog='', errors=[]):
    job = std_q.enqueue('jobs.alerting_task.do_send_to_sentry', products_list, catalog, errors)
    return job.id


"""
Scheduled tasks
"""

# scheduled tasks have a low priority
scheduler = Scheduler('low', connection=redis_conn) # Get a scheduler for the "foo" queue

scheduler.schedule(
    scheduled_time=datetime.utcnow(), # Time for first execution, in UTC timezone
    func=do_cleanup,               # Function to be queued
    args=[config.ENV.CLEANUP_ZONES_LIST, config.ENV.CLEANUP_REPS_AFTER_X_DAYS],  # Arguments passed into function when executed
    # kwargs={'foo': 'bar'},       # Keyword arguments passed into function when executed
    interval=86400,                # 1 day, Time before the function is called again, in seconds
    repeat=None,                   # Repeat this number of times (None means repeat forever)
    # meta={'foo': 'bar'}          # Arbitrary pickleable data on the job itself
)
