#!/usr/bin/env bash

require() {
  local what="$1"
  if ! command -v "$what" >/dev/null; then
    echo "Please install '$what'"
    false
  fi
}

set -e

require tidy
require parallel

cd ~/working/tmp/diving/
find gallery sites taxonomy timeline -name '*.html' -delete

DIVING_VERIFY=1 python3 ~/google_drive/code/python/diving/gallery.py

html_lint="$(
  {
    parallel -n 50 tidy -q -e ::: \
      index.html \
      detective/*.html \
      gallery/*.html \
      sites/*.html \
      taxonomy/*.html \
      timeline/index.html \
      2>&1

    parallel -n 50 tidy -q -e ::: \
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
