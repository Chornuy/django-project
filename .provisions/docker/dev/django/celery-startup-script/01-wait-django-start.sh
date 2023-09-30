#!/bin/bash

until $(curl --output /dev/null --silent --get --fail "${DJANGO_SERVICE_HEALTH_URL}"); do
    printf '.'
    printf 'Waiting django to start'
    sleep 5
done
