#!/bin/bash


# wait for for Elastic to be started
scripts/wait-for-elastic.sh $ES_HOST -- echo "----- Starting gunicorn -----"

# start the server after data has been initialized
# the gunicorn params can be passed as environment variables prefixed with GUNICORN_ and UPPERCASE
# example :
# 	GUNICORN_BIND=0.0.0.0:1378 --> corresponds to --bind 0.0.0.0:1378
# 	GUNICORN_WORKERS=2 --> corresponds to --workers 2
/usr/local/bin/gunicorn --config conf/gunicorn.conf.py main:app \
	--log-level=info \
  --reload \
  --preload \
	--worker-class sanic.worker.GunicornWorker

# NB : --preload will help debugging boot issues
