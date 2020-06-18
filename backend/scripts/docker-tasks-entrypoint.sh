#!/bin/bash

# start RQ Scheduler
# name is generated with a datefield to avoid issue https://github.com/rq/django-rq/issues/296
export name=backend_$(date +%s)
rqworker high default low --url redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT} --name $name 
