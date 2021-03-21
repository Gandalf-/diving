#!/bin/bash

what="$1"
[[ $what ]] || what=style.css

mkdir -p /tmp/cache-check

{
  echo -n 'local        '
  sha1sum "$what"
} > /tmp/cache-check/1 &

{
  echo -n 'space        '
  curl --silent https://diving.sfo2.digitaloceanspaces.com/"$what" \
    | sha1sum
} > /tmp/cache-check/2 &

{
  echo -n 'local-to-cdn '
  curl --silent https://diving.sfo2.cdn.digitaloceanspaces.com/"$what" \
    | sha1sum
} > /tmp/cache-check/3 &

{
  echo -n 'birch-to-cdn '
  ssh birch \
    curl --silent https://diving.sfo2.cdn.digitaloceanspaces.com/"$what" \
    | sha1sum
} > /tmp/cache-check/4 &

{
  echo -n 'alpine       '
  curl --silent --insecure \
    --connect-to diving.anardil.net:443:alpine.anardil.net:443 \
    https://diving.anardil.net/"$what" \
    | sha1sum
} > /tmp/cache-check/5 &

wait

cat /tmp/cache-check/*
