#!/bin/bash

# This is ran every six hours in production.

previous_instance_active () {
  pgrep -a sh | grep -v "^$$ " | grep --quiet 'analyze_new'
}

if previous_instance_active
then
  date +'PID: $$ Previous instance is still active at %H:%M:%S, aborting ... '
else
  cd /home/winrid/govscent
  python3 -m venv env
  source env/bin/activate
  python3.10 manage.py runscript analyze_bills --script-args False
fi
