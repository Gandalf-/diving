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
  log /opt/homebrew/opt/ffmpeg@6/bin/ffmpeg "$@"
}

ffprobe() {
  # ???
  log /opt/homebrew/opt/ffmpeg@6/bin/ffprobe "$@"
}

generate_image_thumbnail() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  log magick \
    "$fin" \
    -strip \
    -interlace plane \
    -resize 350 \
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

generate_video_thumbnail() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  dimensions() {
    # https://www.bannerbear.com/blog/how-to-crop-resize-a-video-using-ffmpeg/
    ffprobe \
      -v error \
      -select_streams v:0 \
      -show_entries stream=width,height \
      -of csv=s=x:p=0 \
      "$1" 2>/dev/null
  }

  declare -A sizes
  sizes[1920x1080]=1440:1080  # mov, sony
  sizes[1280x720]=960:720     # mp4
  sizes[320x240]=320:240      # mp4, old camera

  rescale() {
    local size; size="$( dimensions "$fin" )"
    local target="${sizes[$size]}"
    [[ -z $target ]] && die "unexpected video size $size"

    # https://superuser.com/a/624564
    # https://stackoverflow.com/a/52675535
    # Not sure why I need to flip the scale for Lightroom exports
    ffmpeg \
      -loglevel fatal \
      -noautorotate \
      -nostdin \
      -threads 1 \
      -i "$fin" \
      -ss 2 -t 4 \
      -vf "crop=$target, scale=300:224" \
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
      -threads 1 \
      -loglevel fatal \
      -noautorotate \
      -f webm -i pipe: \
      -filter_complex "$filter" \
      -f webm pipe:
  }

  mp4() {
    ffmpeg \
      -loglevel fatal \
      -noautorotate \
      -f webm -i pipe: \
      -an -c:v libx264 -profile:v main \
      -movflags faststart \
      -vf "format=yuv420p, fps=30" \
      -crf 26 \
      "$fout"
  }

  # ffmpeg is easy 😵
  # https://stackoverflow.com/a/45902691
  rescale \
    | fade \
    | mp4 || die "ffmpeg thumbnail failure $fin"
  report "video $( basename "$fin" )"
}

generate_video_fullsize() {
  local fin="$1"
  local fout="$2"
  [[ -f "$fout" ]] && return

  webm() {
    ffmpeg \
      -nostdin \
      -loglevel fatal \
      -i "$fin" \
      -an \
      -c:v libvpx-vp9 \
      -deadline good \
      -crf 40 \
      -f webm pipe:
  }

  mp4() {
    ffmpeg \
      -loglevel fatal \
      -f webm -i pipe: \
      -movflags faststart \
      -crf 28 \
      "$fout"
  }

  webm \
    | mp4 \
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
