import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectRocket.settings")

# Configure Celery to use Redis as both broker and result backend
app = Celery("projectRocket")
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Explicitly register the tasks module
app.autodiscover_tasks(["apps.tasks"])

