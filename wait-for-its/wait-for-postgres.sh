#!/bin/bash

set -e

host="$1"
shift
cmd="$@"

until psql -h "$host" -U "postgres" -c '\l'; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done

>&2 echo "Database is up - executing command"
exec $cmd

exit 0
