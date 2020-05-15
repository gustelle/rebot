#!/bin/bash

echo "Sceduling of all spiders"

# deploy this crawler for instance
scrapyd-client -t http://localhost:6800 schedule -p estate_agents \*

echo "Spiders scheduled"
