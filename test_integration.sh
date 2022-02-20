#!/bin/bash

set -e

cd ~/working/tmp/diving/

find gallery sites taxonomy timeline -name '*.html' -delete

python3 ~/google_drive/code/python/diving/gallery.py

html_lint="$(
  {
    tidy -q -e \
      index.html \
      detective/*.html \
      gallery/*.html \
      sites/*.html \
      taxonomy/*.html \
      timeline/index.html \
      2>&1

    tidy -q -e \
      timeline/20*.html \
      2>&1 \
      | grep -v 'inserting implicit .body.' \
      | grep -v 'inserting missing .title. element' \
      | grep -v 'missing ..DOCTYPE. declaration'
  } \
    | grep -v '.img. proprietary attribute .loading.' \
    | cut -d ' ' -f 6- \
    | sort \
    | uniq -c
)"

if [[ $html_lint ]]; then
  echo "$html_lint"
  false
fi
