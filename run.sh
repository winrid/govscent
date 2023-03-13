#!/bin/bash
# The orchestrator runs this file post-deployment.

python3.10 -m venv env
source env/bin/activate
pip install -r requirements.txt

python3.10 manage.py migrate
/home/winrid/govscent/env/bin/gunicorn \
          --access-logfile - \
          --workers 4 \
          --bind unix:/run/gunicorn.sock \
          govscent.wsgi:application
