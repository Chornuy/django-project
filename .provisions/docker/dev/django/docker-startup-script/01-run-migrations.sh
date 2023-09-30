#!/bin/bash

# Check if there are migration that need to apply
# Command return not zero if there are not applied migrations
not_applied_migration_exist=$(python manage.py migrate --check)


if ! $not_applied_migration_exist ; then
  # Run migration if there are not applied migration
  python manage.py migrate
fi
