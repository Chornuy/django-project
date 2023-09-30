#!/usr/bin/env bash
SERVICE_NAME=django


if [ -z `docker-compose ps -q $SERVICE_NAME` ] || [ -z `docker ps -q --no-trunc | grep $(docker-compose ps -q $SERVICE_NAME)` ]; then
  echo "No, it's not running."
  docker compose run django python manage.py migrate
else
  echo "Yes, it's running."
  docker compose exec django python manage.py migrate
fi
