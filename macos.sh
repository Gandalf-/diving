#!/usr/bin/env bash

set -e

www=$HOME/working/object-publish/diving-web
src=$HOME/google_drive/code/shell/diving

start_database() {
  # shellcheck disable=SC2317
  cleanup() {
    (( pid )) || return;
    (
      sleep 1.1
      kill "$pid"
    ) &
    disown
  }
  trap cleanup EXIT

  pgrep apocrypha-server >/dev/null &&
    return

  apocrypha-server \
    --headless \
    --database "$src"/data/db.json &

  pid=$!
  until d --keys | grep -q .; do
    sleep 0.1
  done
}

clean() {
  cd "$www"
  find gallery sites taxonomy timeline -name '*.html' -delete
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

wikipedia() {
  start_database

  echo ">>> updater()"
  python3 -i "$src"/information.py
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

dev() {
  echo *.py util/*.py web/* data/*.yml \
    | tr ' ' '\n' \
    | entr bash macos.sh build
}

sitemap() {
  images() {
    rg \
      --sort path \
      --only-matching '/imgs/.*.webp' \
      --glob '*.html' \
      taxonomy sites gallery
  }

  cd "$www"
  images | awk -f "$src"/util/sitemap.awk > sitemap.xml
  xmllint --noout sitemap.xml
}

"$@"
