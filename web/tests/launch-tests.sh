#!/bin/bash

# extract firebase credentials
echo "$FIREBASE_SERVICE_KEY" | base64 --decode --ignore-garbage > "/app/conf/firebase-service-key.json"
export FIREBASE_CONFIG=$(<"/app/conf/firebase-service-key.json")

# run tests
# python -m pytest -v --testdox -s
python -m pytest tests/blueprints/test_products.py::test_list_filter_feature  -vv --testdox -s
# python -m pytest tests/services/data/test_data_provider.py::TestProductService::test_find_sorting -vv --testdox -s
