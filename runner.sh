#!/bin/bash

# timeline html builder. the index page lazy loads the dives in reverese
# chronological order

# shellcheck disable=SC2155

case $(uname) in
  FreeBSD) max_workers=30; sha="sha1 -r" ;;
  Darwin)  max_workers=8;  sha=shasum    ;;
  *)       max_workers=8;  sha=sha1sum   ;;
esac

report() { echo "$@" >&2; }
die() { report "$@"; exit 1; }
debug() { (( DEBUG )) && report "$@"; }

generate_thumbnail() {
  # regenerate the thumbnail if needed

  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  convert \
    -strip \
    -interlace plane \
    -resize 350 \
    -quality 60% \
    "$fin" \
    "$fout" || die "convert failure $fin"
  report "resized $( basename "$fin" )"
}

generate_original() {
  # regenerate the optimized original if needed

  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  convert \
    -strip \
    -quality 35 \
    "$fin" \
    "$fout" || die "convert failure $fin"

  # jpegoptim \
  #   --strip-all \
  #   --all-progressive \
  #   --size 512 \
  #   --quiet \
  #   --stdout \
  #   "$fin" \
  #   > "$fout" || die "jpegoptim failure $fin"
  report "optimized $( basename "$fin" )"
}

scanner() {
  local root="$( realpath "$2" )"
  local size=$(( ${#root} + 2 ))
  local workers=0

  local thumbroot="$( realpath "$PWD" )/imgs"
  local imageroot="$( realpath "$PWD" )/full"
  mkdir -p "$thumbroot" "$imageroot"

  local newest; newest="$(
    # shellcheck disable=SC2010
    ls -Rt "$thumbroot" | grep -vF "$thumbroot" | head -n 1
  )"
  newest="$thumbroot/$newest"
  debug "$newest"

  case $1 in
    fast)
      producer() {
        while read -r path; do
          case $path in
            *.jpg)
              # this image changed
              echo "$path"
              ;;

            *)
              # this directory changed, scan its contents
              for sub in "$path"/*.jpg; do
                echo "$sub"
              done
              printf '%0*d%s\n' $(( size - 1 )) 0 'FOUND_RENAME'
              ;;
          esac
        done < <(
          find "$root" \( -name '*.jpg' -o -type d \) -newer "$newest"
        ) | cut -c "$size"- | sort | uniq
      }
      ;;

    full)
      producer() {
        find "$root" -type f -name '*.jpg' | cut -c "$size"-
      }
      ;;
  esac

  while read -r path; do
    [[ $path == FOUND_RENAME ]] && {
      touch "$newest"
      continue
    }

    [[ $path == '*.jpg' ]] &&
      continue

    (
      local directory="$( dirname "$path" )"
      local image="$( basename "$path" )"

      # get the sha1sum of the original
      local hashed; hashed="$( $sha "$root/$path" )" || die "hash failure $path"
      hashed="${hashed%% *}"
      local unique="$hashed"
      report "hashed $path"

      # update the database for python
      local label="${image%% *}"
      label="${label%%.*}"
      label="$directory:$label"
      d diving cache "$label" hash = "$hashed" </dev/null

      generate_thumbnail "$root/$path" "$thumbroot/$unique.webp"
      generate_original  "$root/$path" "$imageroot/$unique.webp"
    ) &

    (( workers++ ))
    while (( workers > max_workers )); do
      sleep 0.1
      workers="$( jobs -r | wc -l )"
    done

  done < <( producer )
  wait
}

copy_web() {
  local web; web="$( dirname "$( realpath "${BASH_SOURCE[0]}" )" )"/web
  rsync --archive "$web"/ "$PWD"
}

copy_web
scanner fast "$@"
