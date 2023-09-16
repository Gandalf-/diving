#!/bin/bash

# timeline html builder. the index page lazy loads the dives in reverese
# chronological order

# shellcheck disable=SC2155

set -o pipefail

case $(uname) in
  FreeBSD) max_workers=30; sha="sha1 -r" ;;
  Darwin)  max_workers=8;  sha=shasum    ;;
  *)       max_workers=8;  sha=sha1sum   ;;
esac

report() { echo "$@" >&2; }
die()    { report "$@"; exit 1; }
debug()  { (( DEBUG )) && report "$@"; }

generate_image_thumbnail() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  convert \
    -strip \
    -interlace plane \
    -resize 350 \
    -quality 60% \
    "$fin" \
    "$fout" || die "convert thumbnail failure $fin"
  report "thumbnail $( basename "$fin" )"
}

generate_image_fullsize() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  convert \
    -strip \
    -quality 35 \
    "$fin" \
    "$fout" || die "convert fullsize failure $fin"
  report "fullsize $( basename "$fin" )"
}

generate_video_thumbnail() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  rescale() {
    # https://superuser.com/a/624564
    # https://stackoverflow.com/a/52675535
    ffmpeg \
      -loglevel fatal \
      -nostdin \
      -i "$fin" \
      -ss 2 -t 4 \
      -an -c:v libvpx-vp9 -deadline good -crf 40 \
      -vf 'crop=1440:1080,scale=225:300' \
      -f webm pipe:
  }

  fade() {
    # https://stackoverflow.com/a/64907131
    # https://trac.ffmpeg.org/wiki/Xfade
    local filter="\
    [0]trim=end=1,setpts=PTS-STARTPTS[begin];
    [0]trim=start=1,setpts=PTS-STARTPTS[end];
    [end][begin]xfade=distance:duration=1:offset=2"

    ffmpeg \
      -f webm \
      -i pipe: \
      -loglevel fatal \
      -filter_complex "$filter" \
      "$fout"
  }

  # ffmpeg is easy 😵
  # https://stackoverflow.com/a/45902691
  rescale | fade || die "ffmpeg thumbnail failure $fin"
  report "video thumbnail $( basename "$fin" )"
}

generate_video_fullsize() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  ffmpeg \
    -nostdin \
    -loglevel fatal \
    -i "$fin" \
    -an \
    -c:v libvpx-vp9 \
    -deadline good \
    -crf 40 \
    "$fout" || die "ffmpeg fullsize failure $fin"

  report "video fullsize $( basename "$fin" )"
}

scanner() {
  local root="$( realpath "$2" )"
  local size=$(( ${#root} + 2 ))
  local workers=0

  local base="$( realpath "$PWD" )"
  local thumbroot="$base/imgs"
  local imageroot="$base/full"
  local clipsroot="$base/clips"
  local videoroot="$base/video"
  mkdir -p "$thumbroot" "$imageroot" "$clipsroot" "$videoroot"

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
            *.jpg|*.mov)
              # this image changed
              echo "$path"
              ;;

            *)
              # this directory changed, scan its contents
              for sub in "$path"/*.jpg "$path"/*.mov; do
                echo "$sub"
              done
              printf '%0*d%s\n' $(( size - 1 )) 0 'FOUND_RENAME'
              ;;
          esac
        done < <(
          find "$root" \( -name '*.jpg' -o -name '*.mov' -o -type d \) -newer "$newest"
        ) | cut -c "$size"- | sort | uniq
      }
      ;;

    full)
      producer() {
        # find "$root" -type f -name '*.jpg' -o -name '*.mov' | cut -c "$size"-
        find "$root" -type f -name '*.mov' | cut -c "$size"-
      }
      ;;
  esac

  while read -r path; do
    [[ $path == FOUND_RENAME ]] && {
      touch "$newest"
      continue
    }

    [[ $path == '*.jpg' || $path == '.mov' ]] &&
      continue

    [[ -f "$root/$path" ]] ||
      die "$root/$path does not exist!"

    (
      local directory image
      directory="$( dirname "$path" )" || die "dirname failure $path"
      image="$( basename "$path" )" || die "basename failure $path"

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

      if [[ $path =~ .jpg ]]; then
        generate_image_thumbnail "$root/$path" "$thumbroot/$unique.webp"
        generate_image_fullsize  "$root/$path" "$imageroot/$unique.webp"
      else
        generate_video_thumbnail "$root/$path" "$clipsroot/$unique.webm"
        generate_video_fullsize  "$root/$path" "$videoroot/$unique.webm"
      fi
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
scanner full "$@"
