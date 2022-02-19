#!/bin/bash

set -e

cd ~/working/tmp/diving/
python3 ~/google_drive/code/python/diving/gallery.py

tidy -q -e ./**/*.html 2>&1 | cut -d ' ' -f 6- | sort | uniq -c
# tidy -q -e ./**/*.html
