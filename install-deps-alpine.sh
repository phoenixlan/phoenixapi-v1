#!/bin/sh
set -e

echo "Installing dependencies(Alpine"

rm -r staticContent 
rm -r docker

# Runtime dependencies
apk add --no-cache postgresql-libs libpng libjpeg;
# Build-time dependencies
apk add --no-cache --virtual .build-deps build-base libffi-dev postgresql-dev jpeg-dev zlib-dev libpng-dev;

# Pip dependencies
pip install -e . 
# Hack??
pip install psycopg2

mv alembic-docker.ini alembic.ini

# Set up uploads directory
mkdir /uploads 
chown phoenixRest /uploads

# Uninstall build dependencies
apk del .build-deps