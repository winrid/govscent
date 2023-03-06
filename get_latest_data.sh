#!/bin/bash


usc-run govinfo --collections=BILLS --storehtml,text --bulkdata=False
python manage.py runscript usa_import_bills --email-exception --script-args /home/winrid/dev/congress/data False
