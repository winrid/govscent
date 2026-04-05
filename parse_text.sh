#!/bin/bash

python3 -m venv env
source env/bin/activate
python3.10 manage.py runscript usa_import_bills --script-args /home/winrid/congress/data True True False
