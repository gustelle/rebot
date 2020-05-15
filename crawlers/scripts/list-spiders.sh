#!/bin/bash

scrapyd_service="$1"

scrapyd-client -t http://localhost:6800 spiders -p estate_agents
# scrapyd-client -t http://134.209.166.111:6800 spiders -p estate_agents
# curl "$scrapyd_service/listspiders.json?project=catalog_crawlers"
