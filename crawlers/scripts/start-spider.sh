#!/bin/bash

spider="$1"

echo "Deployment of spider $1 requested"

# deploy this crawler for instance
# scrapyd-client -t http://134.209.166.111:6800 schedule -p estate_agents $spider
scrapyd-client -t http://localhost:6800 schedule -p estate_agents $spider

echo "Spider $1 deployed and scheduled"
