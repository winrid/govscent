#!/bin/bash
# The orchestrator runs this file post-deployment.

python3.10 -m venv env
source env/bin/activate
pip install -r requirements.txt

python3.10 manage.py migrate
python3.10 manage.py collectstatic --skip-checks
/home/winrid/govscent/env/bin/gunicorn \
          --access-logfile - \
          --workers 4 \
          govscent.wsgi:application
