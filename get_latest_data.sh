#!/bin/bash

# This is ran every six hours in production.

previous_instance_active () {
  pgrep -a sh | grep -v "^$$ " | grep --quiet 'get_latest_data'
}

if previous_instance_active
then
  date +'PID: $$ Previous instance is still active at %H:%M:%S, aborting ... '
else
  cd /home/winrid/congress
  python3 -m venv env
  source env/bin/activate
  usc-run govinfo --collections=BILLS --store=html

  cd /home/winrid/govscent
  python3 -m venv env
  source env/bin/activate
  python3.10 manage.py runscript usa_import_bills --script-args /home/winrid/congress/data False False
fi
