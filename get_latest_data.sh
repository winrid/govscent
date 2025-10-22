#!/bin/bash

cd /home/winrid/congress || exit
source env/bin/activate
usc-run govinfo --collections=BILLS --store=html

cd /home/winrid/govscent || exit
source env/bin/activate
python3 manage.py runscript usa_import_bills --script-args /home/winrid/congress/data False False
