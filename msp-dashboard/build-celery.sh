#!/usr/bin/env bash

# Run the celery worker
celery -A projectRocket worker --loglevel=info
