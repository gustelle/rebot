#!/bin/bash

# extract firebase credentials
echo "$FIREBASE_SERVICE_KEY" | base64 --decode --ignore-garbage > "/app/conf/firebase-service-key.json"
export FIREBASE_CONFIG=$(<"/app/conf/firebase-service-key.json")

# run tests
python -m pytest -v --testdox -s
# python -m pytest tests/services/test_user_service.py::test_save_firstname -vv --testdox -s
