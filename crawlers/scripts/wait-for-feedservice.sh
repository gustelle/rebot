#!/bin/bash

set -e

host="$1"
shift
cmd="$@"

echo "Waiting for service $host to be available"


# First wait for the service to be started...
response=$(curl $host)

until [ "$response" = "200" ]; do
    response=$(curl --write-out %{http_code} --silent --output /dev/null "$host")
    >&2 echo "Feed Service unavailable - sleeping"
    sleep 1
done

# next wait for the health to return {'success': true}
json_health_response="$(curl -fsSL "$host")"
json_health_response="$(echo "$json_health_response")" # remove double quotes

# the regexp will try to match {"success": true} in the JSON response
regex='["]?success["]?[[:space:]]?:[[:space:]]?true'

until [[ "$json_health_response" =~ $regex ]]; do
    json_health_response=$(curl -fsSL "$host")
    echo "Unhealthy service ($json_health_response), waiting for a healthy status"
    sleep 1
done

>&2 echo "Feed Service is now healthy"
exec $cmd