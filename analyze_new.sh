#!/bin/bash

cd /home/winrid/govscent || exit
source env/bin/activate
python3.10 manage.py runscript analyze_bills --script-args False
