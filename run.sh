#!/bin/bash
# The orchestrator runs this file post-deployment.

python manage.py migrate
/home/winrid/govscent/venv/bin/gunicorn \
          --access-logfile - \
          --workers 4 \
          --bind unix:/run/gunicorn.sock \
          govscent.wsgi:application
