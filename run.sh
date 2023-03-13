#!/bin/bash
# The orchestrator runs this file post-deployment.

python3 manage.py migrate
/home/winrid/govscent/env/bin/gunicorn \
          --access-logfile - \
          --workers 4 \
          --bind unix:/run/gunicorn.sock \
          govscent.wsgi:application
