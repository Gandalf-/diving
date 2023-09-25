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
  bash    "$src"/util/runner.sh  ~/Pictures/diving/
  python3 "$src"/gallery.py      ~/Pictures/diving/
}

prune() {
  start_database
  cd "$www"

  expected-keys() {
    (
      cd ~/Pictures/diving || exit 1
      find . -type f \
        | awk '
      BEGIN { FS="/"; OFS=":" }
      /jpg|mov|mp4/ {
        gsub(/ - .*/, "");
        gsub(/\....$/, "");
        print $2, $3
      }' \
        | sort
    )
  }

  actual-keys() {
    d diving cache --keys | sort
  }

  stale-keys() {
    while read -r key; do
      echo d diving cache "$key" -d
      d diving cache "$key" -d </dev/null
    done < <(
      comm -1 -3 <( expected-keys ) <( actual-keys )
    )
  }

  expected-hashes() {
    d diving cache \
      | awk '/"hash"/ { gsub(/"/, ""); print $2 }' \
      | sort -u
  }

  actual-hashes() {
    (
      cd "$www" || exit 1
      find imgs full clips video -type f \
        | cut -d / -f 2 \
        | cut -d . -f 1 \
        | grep . \
        | sort -u
    )
  }

  stale-hashes() {
    while read -r fingerprint; do
      rm -v "$www"/*/"$fingerprint"*
    done < <(
      comm -1 -3 <( expected-hashes ) <( actual-hashes )
    )
  }

  stale-keys
  stale-hashes
}

wikipedia() {
  start_database

  echo ">>> updater()"
  python3 -i "$src"/information.py
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
    | entr bash util/macos.sh build
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
