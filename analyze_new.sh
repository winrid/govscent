#!/bin/bash

cd /home/winrid/govscent
python3.10 -m venv env
source env/bin/activate
python3.10 manage.py runscript analyze_bills --script-args False
