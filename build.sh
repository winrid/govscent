#!/bin/bash

#rm -r env
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
