#!/bin/bash
# The orchestrator runs this file post-deployment.

python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

python3 manage.py migrate
python3 manage.py collectstatic --skip-checks --no-input
/home/winrid/govscent/env/bin/gunicorn \
          --access-logfile - \
          --error-logfile - \
          --workers 4 \
          govscent.wsgi:application
