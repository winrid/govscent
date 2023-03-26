#!/bin/bash

# This is ran every six hours in production.

#usc-run govinfo --collections=BILLS --storehtml,text --bulkdata=False

cd /home/winrid/govscent
python3 -m venv env
source env/bin/activate
python3.10 manage.py runscript usa_import_bills --script-args /home/winrid/congress/data False False False
