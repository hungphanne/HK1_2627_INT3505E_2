#!/bin/sh
set -e

echo "Running database migrations..."
flask --app product_api.factory db upgrade

echo "Starting gunicorn..."
exec gunicorn -c gunicorn.conf.py "product_api.factory:create_app()"
