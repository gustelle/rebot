#!/bin/bash

job="$1"

echo "Stop of job $1 requested"

# curl http://134.209.166.111:6800/cancel.json -d project=estate_agents -d job="$job"
curl http://localhost:6800/cancel.json -d project=estate_agents -d job="$job"
