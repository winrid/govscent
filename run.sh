#!/bin/bash
# The orchestrator runs this file post-deployment.

source env/bin/activate
python3 manage.py migrate
/home/winrid/govscent/env/bin/gunicorn \
          --access-logfile - \
          --workers 4 \
          --bind unix:/run/gunicorn.sock \
          govscent.wsgi:application
