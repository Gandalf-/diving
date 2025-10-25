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

log() {
  echo "$@" >> ~/working/tmp/diving.log
  "$@"
}

ffmpeg() {
  # ffmpeg 7 breaks the madness I have going on with xfade
  # [Parsed_xfade_8 @ 0x60000373c9a0] The inputs needs to be a constant frame rate
  # [Parsed_xfade_8 @ 0x60000373c9a0] Failed to configure output pad on Parsed_xfade_8
  log nice -n 10 /opt/homebrew/opt/ffmpeg@6/bin/ffmpeg "$@"
}

ffprobe() {
  # ???
  log /opt/homebrew/opt/ffmpeg@6/bin/ffprobe "$@"
}

choose_smoothing() {
  local fin="$1"
  case "${fin,,}" in
    *seal*|*'sea lion'*)
      report "using low smoothing for $( basename "$fin" )"
      echo 2
      ;;
    *)
      echo 30
      ;;
    esac
}

generate_image_thumbnail() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  log magick \
    "$fin" \
    -strip \
    -interlace plane \
    -resize "350x262^" \
    -gravity center \
    -extent 350x262 \
    -quality 60% \
    "$fout" || die "convert thumbnail failure $fin"
  report "image $( basename "$fin" )"
}

generate_image_fullsize() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  log magick \
    "$fin" \
    -strip \
    -quality 35 \
    "$fout" || die "convert fullsize failure $fin"
  report "IMAGE $( basename "$fin" )"
}

generate_video_transform() {
  local fin="$1"
  local fout="$HOME/working/video-transforms/$( identity "$fin" | awk '{ print $1 }' ).trf"
  [[ -f "$fout" ]] && return

  ffmpeg \
    -nostdin \
    -loglevel error \
    -i "$fin" \
    -vf vidstabdetect=stepsize=24:shakiness=9:accuracy=15:result="$fout" \
    -f null - \
    || die "ffmpeg transform failure $fin"

  report "study $( basename "$fin" )"
}

generate_video_thumbnail() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  dimensions() {
    ffprobe \
      -v error \
      -select_streams v:0 \
      -show_entries stream=width,height \
      -of csv=s=x:p=0 \
      "$1" 2>/dev/null
  }

  declare -A sizes
  sizes[1920x1080]=1440:1080  # mp4, sony
  sizes[1280x720]=960:720     # mov, olympus tg-6
  sizes[320x240]=320:240      # mp4, olympus old

  local size; size="$( dimensions "$fin" )"
  local crop_target="${sizes[$size]}"
  [[ -z "$crop_target" ]] && die "unexpected video size $size"

  local transforms="$HOME"/working/video-transforms/"$( identity "$fin" | awk '{ print $1 }' )".trf
  [[ -f $transforms ]] || die "missing transform file $transforms"
  local smoothing="$( choose_smoothing "$fin" )"

  local filter_graph="
    [0:v]
    vidstabtransform=input=$transforms:smoothing=$smoothing:optzoom=1:interpol=bicubic,
    crop=$crop_target,
    scale=300:224,
    split [main][loop];

    [main]trim=start=1,setpts=PTS-STARTPTS [end];
    [loop]trim=end=1,setpts=PTS-STARTPTS [begin];

    [end][begin]xfade=transition=fade:duration=1:offset=2,
    format=yuv420p,
    fps=30
    [outv]"

  ffmpeg \
    -loglevel fatal \
    -nostdin \
    -ss 2 -i "$fin" \
    -t 4 \
    -filter_complex "$filter_graph" \
    -map "[outv]" \
    -an \
    -c:v libx264 \
    -profile:v main \
    -crf 26 \
    -movflags +faststart \
    "$fout" \
    || die "ffmpeg thumbnail failure $fin"

  report "video $( basename "$fin" )"
}

generate_video_fullsize() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  local transforms="$HOME"/working/video-transforms/"$( identity "$fin" | awk '{ print $1 }' )".trf
  local smoothing="$( choose_smoothing "$fin" )"
  local staboptions="smoothing=$smoothing:optzoom=1:interpol=bicubic"
  [[ -f $transforms ]] || die "missing transform file $transforms"

  ffmpeg \
    -loglevel fatal \
    -nostdin \
    -i "$fin" \
    -vf "vidstabtransform=input=$transforms:$staboptions" \
    -c:v libx264 \
    -crf 28 \
    -pix_fmt yuv420p \
    -an \
    -movflags +faststart \
    "$fout" \
    || die "ffmpeg fullsize failure $fin"

  report "VIDEO $( basename "$fin" )"
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
            */diving)
              # not interested in whether the root changed
              continue
              ;;

            *.jpg)
              # this image changed
              echo "$path"
              ;;

            *)
              # this directory changed, scan its contents
              for sub in "$path"/*.{jpg,mov,mp4}; do
                [[ -f "$sub" ]] || continue
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
        find "$root" \
          -name '*.jpg' -o \
          -name '*.mov' -o \
          -name '*.mp4' \
          | cut -c "$size"-
      }
      ;;

    video)
      producer() {
        find "$root" \
          -name '*.mov' -o \
          -name '*.mp4' \
          | cut -c "$size"-
      }
      ;;
  esac

  while read -r path; do
    [[ $path == FOUND_RENAME ]] && {
      touch "$newest"
      continue
    }

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
      report "check $path"

      # update the database for python
      local label="${image%% *}"
      label="${label%%.*}"
      label="$directory:$label"
      d diving cache "$label" hash = "$hashed" </dev/null

      if [[ $path =~ .jpg ]]; then
        generate_image_thumbnail "$root/$path" "$thumbroot/$unique.webp"
        generate_image_fullsize  "$root/$path" "$imageroot/$unique.webp"
      else
        generate_video_transform "$root/$path"
        generate_video_thumbnail "$root/$path" "$clipsroot/$unique.mp4"
        generate_video_fullsize  "$root/$path" "$videoroot/$unique.mp4"
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
  local web; web="$( dirname "$( realpath "${BASH_SOURCE[0]}" )" )"/../web
  rsync --archive "$web"/ "$PWD"
}

date > ~/working/tmp/diving.log
copy_web
scanner fast "$@"
