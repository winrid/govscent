#!/bin/bash

# 1. We train a gensim model and create a dictionary from the latest Wikipedia dump: https://dumps.wikimedia.org/enwiki/latest/
# 2. We create and save the dictionary (python -m gensim.scripts.make_wiki)
# TODO In the future we could update these scripts so anyone can run them (remove hard coded paths), assuming the project takes off.

cd /home/winrid/govscent
python3.10 -m venv env
source env/bin/activate
python3.10 -m gensim.scripts.make_wiki ~/enwiki-latest-pages-articles.xml.bz2 ~/govscent-wiki/results 250000
