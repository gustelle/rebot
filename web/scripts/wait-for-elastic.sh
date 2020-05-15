#!/bin/bash

set -e

host="$1"
shift
cmd="$@"

echo "Waiting for $host to be up and running"
echo "-------------------------------------"

until $(curl --output /dev/null --silent --head --fail "$host"); do
    printf '.'
    sleep 1
done

# First wait for ES to start...
response=$(curl $host)

until [ "$response" = "200" ]; do
    response=$(curl --write-out %{http_code} --silent --output /dev/null "$host")
    >&2 echo "Elastic Search is unavailable - sleeping"
    sleep 1
done

echo "Elastic Search is starting"

# next wait for ES status to turn to Green
#echo "Checking $host/_cat/health?h=status"
health="$(curl -fsSL "$host/_cluster/health")"
health="$(echo "$health" | sed -r 's/^[[:space:]]+|[[:space:]]+$//g')" # trim whitespace (otherwise we'll have "green ")

echo "Elastic health: $health"

# until [ "$health" = 'green' ]; do
#     health="$(curl -fsSL "$host/_cat/health?h=status")"
#     health="$(echo "$health" | sed -r 's/^[[:space:]]+|[[:space:]]+$//g')" # trim whitespace (otherwise we'll have "green ")
#     >&2 echo "Elastic Search is unavailable - sleeping"
#     sleep 1
# done

>&2 echo "Elastic Search is up"
exec $cmd
