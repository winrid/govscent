#!/bin/bash

#rm -r env venv
/home/winrid/.pyenv/versions/3.10.10/bin/python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
