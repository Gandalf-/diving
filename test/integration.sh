#!/usr/bin/env bash

require() {
  local what="$1"
  if ! command -v "$what" >/dev/null; then
    echo "Please install '$what'"
    false
  fi
}

start_database() {
  cleanup() {
    [[ $pid ]] || return;
    kill "$pid"
    echo Server stopped
  }
  trap cleanup EXIT

  pgrep apocrypha-server >/dev/null &&
    return

  apocrypha-server \
    --headless \
    --stateless \
    --database ~/google_drive/code/python/diving/data/db.json &

  pid=$!
  until d --keys | grep -q .; do
    sleep 0.1
  done
}

set -e

require tidy
require parallel

mkdir -p ~/working/tmp/diving
cd ~/working/tmp/diving/
find gallery sites taxonomy timeline -name '*.html' -delete

start_database
DIVING_VERIFY=1 python3 ~/google_drive/code/shell/diving/cli.py generate

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
    | grep -v '.video. proprietary attribute .disableremoteplayback.' \
    | grep -v 'trimming empty .span.' \
    | cut -d ' ' -f 6- \
    | sort \
    | uniq -c
)"

if [[ $html_lint ]]; then
  echo "$html_lint"
  false
fi
