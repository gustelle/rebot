#!/bin/bash

# wait for for Feedservice to be started
./wait-for-feedservice.sh $FEED_SERVICE_HEALTH -- echo "Starting scrapyd"

scrapyd
