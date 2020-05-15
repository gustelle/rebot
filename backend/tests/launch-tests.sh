#!/bin/bash

# add /app to the path because test files are under /tests, but tests use modules located in the parent forlder (/app)
export PYTHONPATH=$PYTHONPATH:/app

pytest -vv --testdox -s

# run tests
# python -m pytest tests/jobs/test_elastic_task.py::TestIndexTask::test_city_sanitization -vv --testdox -s
