#!/usr/bin/env bash

set -e

www=$HOME/working/object-publish/diving-web
src=$HOME/google_drive/code/shell/diving

start_database() {
  cleanup() {
    [[ $pid ]] || return;
    kill $pid
    echo Server stopped
  }
  trap cleanup EXIT

  pgrep apocrypha-server >/dev/null &&
    return

  apocrypha-server --headless &
  pid=$!
  until d --keys | grep -q .; do
    sleep 0.1
  done
}

full() {
  start_database

  cd $www
  bash    $src/runner.sh  ~/Pictures/diving/
  python3 $src/gallery.py ~/Pictures/diving/ /fullsize
}

quick() {
  start_database

  cd $www
  python3 $src/gallery.py ~/Pictures/diving/ /fullsize
}

serve() {
  cd $www
  sws --public --local
}

"$@"
