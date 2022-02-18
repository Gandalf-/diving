#!/bin/bash

what="$1"
[[ $what ]] || what=style.css

mkdir -p /tmp/cache-check

check() {
  {
    time "$@" | sha1sum
  } 2>&1 \
    | head -n 3 \
    | grep -v '^$' \
    | paste -d ' ' - - \
    | awk '{print $1, $2, $4}'
}

run() {
  {
    echo -n 'local        '
    sha1sum "$what" | awk '{print $1}'
  } > /tmp/cache-check/1 &

  {
    echo -n 'space        '
    check curl --silent https://diving.sfo2.digitaloceanspaces.com/"$what"
  } > /tmp/cache-check/2 &

  {
    echo -n 'local-to-cdn '
    check curl --silent https://diving.sfo2.cdn.digitaloceanspaces.com/"$what"
  } > /tmp/cache-check/3 &

  {
    echo -n 'birch-to-cdn '
    check ssh birch \
      curl --silent https://diving.sfo2.cdn.digitaloceanspaces.com/"$what"
  } > /tmp/cache-check/4 &

  {
    echo -n 'alpine       '
    check curl --silent --insecure \
      --connect-to diving.anardil.net:443:alpine.anardil.net:443 \
      https://diving.anardil.net/"$what"
  } > /tmp/cache-check/5 &

  wait
  cat /tmp/cache-check/*
}

run
# check curl --silent https://diving.sfo2.cdn.digitaloceanspaces.com/"$what"
