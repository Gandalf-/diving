#!/bin/bash

source /home/leaf/dotfiles/lib/common.sh
cd /home/leaf/working/object-publish/diving-web || exit 1

when="$( date +'%Y-%m-%dT%H:%M' )"
total="$( find . -type f | wc -l )"
step="$(( total / 80 ))"

i=0

fetch() {

  local what="$1"
  local speed; speed="$(
    {
      time curl --silent --head \
        https://diving.sfo2.cdn.digitaloceanspaces.com/"$what"
    } 2>&1 | awk '/real/ { print $2 }'
  )"

  speed="${speed//0m}"
  speed="${speed//s}"

  sleep "$speed"
  d diving cache-speed "$when" + "$speed"

  (( i++ ))
  (( i % step )) || echo "diving prefetch $i/$total"
}

find . -type f -printf '%P\n' \
  | common::map fetch
