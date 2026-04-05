#!/bin/bash

cd /home/winrid/govscent || exit
source env/bin/activate
python3 manage.py runscript analyze_bills --script-args False
python3 manage.py warm_caches
