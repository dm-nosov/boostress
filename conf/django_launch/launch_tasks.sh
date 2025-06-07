#!/bin/bash

# Wait for the database to be ready
until nc -z -v -w30 db 5432
do
  echo "Waiting for the database connection..."
  sleep 1
done

# Inject docker secrets
chmod +x /app/conf/django_secrets/inject_secrets.sh
/app/conf/django_secrets/inject_secrets.sh

# Once the database is ready, run migrations
# Once the database is ready, run migrations
python manage.py migrate


# Start Gunicorn server
exec gunicorn boostress.wsgi:application --bind 0.0.0.0:8000