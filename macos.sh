#!/usr/bin/env bash

set -e

www=$HOME/working/object-publish/diving-web
src=$HOME/google_drive/code/shell/diving

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
    --database ~/google_drive/code/python/diving/data/db.json &

  pid=$!
  until d --keys | grep -q .; do
    sleep 0.1
  done
}

build() {
  start_database

  case $1 in
    -f|--fast) export DIVING_FAST=1 ;;
  esac

  cd "$www"
  bash    "$src"/runner.sh  ~/Pictures/diving/
  python3 "$src"/gallery.py ~/Pictures/diving/
}

serve() {
  cd "$www"
  sws --public --local
}

sync() {
  rsync \
    --exclude .DS_Store \
    --delete \
    --delete-excluded \
    -av --info=progress2 \
    "$www"/ \
    yew:/mnt/ssd/hosts/web/diving/
}

"$@"
