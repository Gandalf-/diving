#!/bin/bash

# timeline html builder. the index page lazy loads the dives in reverese
# chronological order

hasher() {

  local directory="$1"
  local image="$2"

  local label="${image%% *}"
  label="${label%%.*}"
  label="$directory:$label"

  local out; out="$( d diving cache "$label" hash < /dev/null )"

  if [[ $out ]]; then
    echo "$out"
  else
    echo "hashing $directory/$image" >&2
    result="$( $sha "$image" | awk '{print $1}' )"
    d diving cache "$label" hash = "$result" </dev/null
    echo "$result"
  fi
}

maker() {
  [[ $1 && $2 && $3 ]] || {
    echo "usage: path title date" >&2
    exit 1
  }

  local imgbase; imgbase="$( pwd )/imgs"
  local srcbase; srcbase="$( basename "$1" )"

  cd "$1" || {
    echo "$1 doesn't exist" >&2
    exit 1
  }

  mkdir -p "$imgbase"

  for image in *.jpg; do
      local name; name="$( hasher "$srcbase" "$image" ).jpg"

      [[ -f "$imgbase"/"$name" ]] || {
        {
          convert \
            -strip \
            -interlace plane \
            -resize 350 \
            -quality 60% \
            "$image" \
            "$imgbase"/"$name"

          echo "resized $image" >&2
        } &
      }
  done
  wait
}

case $(uname) in
  FreeBSD)
    sha="sha1 -r"
    tac="tail -r"
    ;;
  Darwin)
    sha=shasum
    tac="tail -r"
    ;;
  *)
    sha=sha1sum
    tac=tac
esac

DEBUG=0

main() {

  local target="$1"
  [[ -d "$target" ]] || {
    echo "'$1' doesn't exist" >&2
    exit 1
  }
  local workers=0

  while read -r f; do
    local name date
    name="$( basename "$f" | cut -d ' ' -f 2- | sed -e 's/^[[:digit:]]\s\+//' )"
    date="$( basename "$f" | cut -d ' ' -f 1  )"
    (( DEBUG )) && echo "$name: " >&2

    (
      # subshell because we're changing directories
      maker "$f" "$name" "$date"
      echo -n .
    ) &
    (( workers++ ))

    while (( workers > 16 )); do
      sleep 0.1
      workers="$( jobs -r | wc -l )"
    done

  done < <(
    for z in "$target"/*; do
      echo "$z"
    done | $tac
  )

  wait
  echo
}

main "$@"
