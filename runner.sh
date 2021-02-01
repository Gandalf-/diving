#!/bin/bash

# timeline html builder. the index page lazy loads the dives in reverese
# chronological order

print_switcher() {

echo '
    <a href="/taxonomy/index.html">
        <h1 class="top switch taxonomy">Taxonomy</h1>
    </a>
    <div class="top" id="buffer"></div>
    <a href="/timeline/index.html">
        <h1 class="top switch">Timeline</h1>
    </a>
    <div class="top" id="buffer"></div>
    <a href="/gallery/index.html">
        <h1 class="top switch gallery">Gallery</h1>
    </a>
'
}

print_title() {

  local title="$1"
  local date="$2"

  echo "<h1> $title </h1>"
  echo "<h4> $date </h4>"
  echo
}

print_image() {

  local image="$1"
  local thumbnail=/imgs/"${names[$srcbase/$image]}"
  local fullsize="https://public.anardil.net/media/diving/$srcbase/$image"
  local subject=""

  [[ "$image" =~ ' - ' ]] && {
    subject="$image"
    subject="${subject//* - }"
    subject="${subject%%.jpg}"
    (( DEBUG )) && echo -n "$subject, " >&2
  }

  echo '  <a data-fancybox="gallery" data-caption="'"$subject"'" href="'"$fullsize"'">'
  echo '    <img src="'"$thumbnail"'" alt="">'
  echo '  </a>'
}

print_table() {

  echo '<div class="grid">'

  for image in *.jpg; do
    print_image "$image"
  done

  echo '</div>'
}

hasher() {
  local directory="$1"
  local image="$2"

  local label="${image%% *}"
  label="${label%%.*}"
  label="$directory:$label"

  local out; out="$( d diving cache-hash "$label" < /dev/null )"

  if [[ $out ]]; then
    echo "$out"
  else
    echo "hashing $directory/$image" >&2
    $sha "$image" | awk '{print $1}'
  fi
}

maker() {

  [[ $1 && $2 && $3 ]] || {
    echo "usage: path title date"
    exit 1
  }

  local imgbase; imgbase="$( pwd )/imgs"
  local srcbase; srcbase="$( basename "$1" )"

  cd "$1" || exit 1
  declare -A names
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

      names[$srcbase/$image]="$name"
  done
  wait

  print_title "$2" "$3"

  print_table
}


# runs the index.html generation script for each directory under the path
# provided. a single index.html is produced, with the most recent images first.

# todo
# lazy load images when they become visible

print_head() {

  echo '
  <head>
    <title>Diving Timeline</title>
    <link rel="stylesheet" href="/style.css"/>
  </head>
  '
}

print_scripts() {

  echo '
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery.min.js"></script>
    <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
    <script src="/jquery.fancybox.min.js"></script>
  '
}

javascript() {

  local first="${dives[0]}"
  local second="${dives[1]}"
  local third="${dives[2]}"

  # shellcheck disable=SC2016
  echo '
  <script>
    var furthest = 0;

    function loader(elem, content) {
      var top_of_elem = $(elem).offset().top;
      var bot_of_elem = top_of_elem + $(elem).outerHeight();
      var bot_of_scrn = $(window).scrollTop() + window.innerHeight;
      var top_of_scrn = $(window).scrollTop();

      if ((bot_of_scrn < top_of_elem) || (top_of_scrn > bot_of_elem)) {
        // we are not yet nearing the bottom
        return false;
      }

      if ($(elem).hasClass("isloaded")) {
        // the page is already loaded
        return false;
      }

      if (furthest >= bot_of_scrn) {
        // we have gotten further than this before
        return false;
      }

      furthest = bot_of_scrn;
      console.log("loading ", elem)
      $(elem).load(content)
      $(elem).addClass("isloaded");

      return true;
    }

    // preload three groups to fill the screen
    $("#0").load("'"$first"'").addClass("isloaded");
    $("#1").load("'"$second"'").addClass("isloaded");
    $("#2").load("'"$third"'").addClass("isloaded");

    $(window).scroll(function() {
  '

  for ((i=2; i < counter-1; i++)); do
    local html="${dives[$i]}"
    echo "       if (loader('#$i', '$html')) { return; }"
  done

  local last=$(( counter - 1 ))
  local html="${dives[$last]}"

  echo "       if (loader('#$last', '$html')) { return; }"

  echo '
    });

    function jump(place) {
      document.getElementById(place).scrollIntoView(true);
    }

    function openNav() {
      document.getElementById("mySidebar").style.width = "250px";
    }

    function closeNav() {
      document.getElementById("mySidebar").style.width = "0";
    }
  </script>
  '
}

case $(uname) in
  FreeBSD)
    sha="sha1 -r"
    tac="tail -r"
    ;;
  *)
    sha=sha1sum
    tac=tac
esac

counter=0
dives=()
DEBUG=0

main() {

  target="$1"
  [[ -d "$target" ]] || {
    echo "$1 doesn't exist"
    exit 1
  }

  echo '<!DOCTYPE html>'
  echo '<html>'

  print_head

  echo '  <body>'
  print_switcher
  print_scripts

  while read -r f; do
    name="$( basename "$f" | cut -d ' ' -f 2- )"
    date="$( basename "$f" | cut -d ' ' -f 1  )"
    (( DEBUG )) && echo "$name: " >&2

    echo "    <div id='$counter'></div>"

    (
      # subshell because we're changing directories
      maker "$f" "$name" "$date" > tmp.html
    )
    htmlhash="$( $sha < tmp.html | awk '{print $1}' )"
    dives+=( "$htmlhash".html )
    mv tmp.html timeline/"$htmlhash".html

    (( counter++ ))

    (( DEBUG )) && echo >&2
    (( DEBUG )) && echo >&2
  done < <(
    for z in "$target"/*; do
      echo "$z"
    done | $tac
  )

  echo '  </body>'

  javascript
  echo '</html>'
}

main "$@" > timeline/index.html
