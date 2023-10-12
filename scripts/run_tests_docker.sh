#!/usr/bin/env bash

docker compose -f docker-compose.test-flow.yml run --rm django pytest
docker compose -f docker-compose.test-flow.yml stop
