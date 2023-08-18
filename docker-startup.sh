#!/usr/bin/env sh

echo "Waiting for DB to fire up...."
./wait-for-it.sh db:5432
echo "Db started"

sleep 4
ls -l
/usr/local/bin/alembic upgrade heads

echo "Hello world"

set -e
echo "Running $@"

"$@"