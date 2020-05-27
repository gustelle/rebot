#!/bin/bash

# extract firebase credentials
echo "$FIREBASE_SERVICE_KEY" | base64 --decode --ignore-garbage > "/app/conf/firebase-service-key.json"
export FIREBASE_CONFIG=$(<"/app/conf/firebase-service-key.json")

# run tests
python -m pytest -v --testdox -s
# python -m pytest tests/blueprints/test_users.py -vv --testdox -s
