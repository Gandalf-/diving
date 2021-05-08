#!/bin/bash

source /home/leaf/dotfiles/lib/common.sh
cd /home/leaf/working/object-publish/diving-web || exit 1

total="$( find . -type f | wc -l )"
step="$(( total / 80 ))"

echo '|..............................................................................|'

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
  d diving cache-speed + "$speed"

  (( i++ ))
  (( i % step )) || echo -n .
}

d diving cache-speed -d

find . -type f -printf '%P\n' \
  | common::map fetch

echo
