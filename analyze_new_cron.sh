#!/bin/bash

# This is ran every six hours in production.

previous_instance_active () {
  pgrep -a sh | grep -v "^$$ " | grep --quiet 'analyze_new.sh'
}

if previous_instance_active
then
  date +'PID: $$ Previous instance is still active at %H:%M:%S, aborting ... '
else
  ./analyze_new.sh
fi
