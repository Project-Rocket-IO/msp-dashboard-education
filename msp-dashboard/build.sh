#!/usr/bin/env bash

# Create log directory if it doesn't exist
mkdir -p /var/log/django

# Run the command to create the database
python manage.py collectstatic --noinput

# Run the command to migrate the database
python manage.py migrate --noinput

# Run the command to set groups and permissions
python manage.py loaddata groups.json

# Run the application with Gunicorn
gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 2 --timeout 0 projectRocket.wsgi:application