#!/bin/bash

set -e

cd ~/working/tmp/diving/
python3 ~/google_drive/code/python/diving/gallery.py

tidy -q -e \
  index.html \
  detective/*.html \
  gallery/*.html \
  sites/*.html \
  taxonomy/*.html \
  timeline/index.html \
  2>&1 | cut -d ' ' -f 6- | sort | uniq -c
