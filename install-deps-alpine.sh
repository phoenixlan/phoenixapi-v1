#!/bin/sh
set -e

rm -r staticContent 
rm -r docker

echo "Installing dependencies(Alpine)"

# Runtime dependencies
apk add --no-cache postgresql-libs tk libpng libjpeg;
# Build-time dependencies
apk add --no-cache --virtual .build-deps build-base libffi-dev postgresql-dev jpeg-dev zlib-dev libpng-dev;

echo "Installing pip dependencies"
# Pip dependencies
pip install -e . 
# Hack??
pip install psycopg2

echo "Cleaning up..."
mv alembic-docker.ini alembic.ini

# Uninstall build dependencies
apk del .build-deps