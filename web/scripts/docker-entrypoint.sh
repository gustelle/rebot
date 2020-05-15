#!/bin/bash

# extract firebase credentials
echo "$FIREBASE_SERVICE_KEY" | base64 --decode --ignore-garbage > "/app/conf/firebase-service-key.json"
export FIREBASE_CONFIG=$(<"/app/conf/firebase-service-key.json")

# wait for for Elastic to be started
/app/scripts/wait-for-elastic.sh $ES_HOST -- echo "----- Starting gunicorn -----"


# start the server after data has been initialized
# the gunicorn params can be passed as environment variables prefixed with GUNICORN_ and UPPERCASE
# example :
# 	GUNICORN_BIND=0.0.0.0:1378 --> corresponds to --bind 0.0.0.0:1378
# 	GUNICORN_WORKERS=2 --> corresponds to --workers 2
/usr/local/bin/gunicorn --config /app/conf/gunicorn.conf.py main:app \
	--log-level=info \
  --reload \
  --preload \
	--worker-class sanic.worker.GunicornWorker

# NB : --preload will help debugging boot issues
