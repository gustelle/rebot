#!/bin/bash

# extract firebase credentials
echo "$FIREBASE_SERVICE_KEY" | base64 --decode --ignore-garbage > "/app/conf/firebase-service-key.json"
export FIREBASE_CONFIG=$(<"/app/conf/firebase-service-key.json")

# start RQ Scheduler
# name is generated with a datefield to avoid issue https://github.com/rq/django-rq/issues/296
export name=web_$(date +%s)
rqworker high default low --url redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT} --name $name -c settings.sentry
