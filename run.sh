#!/bin/bash
# The orchestrator runs this file post-deployment.

python manage.py migrate
# TODO server
