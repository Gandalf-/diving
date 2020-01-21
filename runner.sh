#!/bin/bash

# build the html for a single dive entry. this handles resizing and compressing
# images for better data usage performance


print_title() {

  local title="$1"
  local date="$2"

  echo "<h1> $title </h1>"
  echo "<h4> $date </h4>"
  echo
}

print_image() {

  local image="$1"
  local thumbnail=imgs/"${names[$srcbase/$image]}"
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

print_menu() {
  echo '
    <div id="mySidebar" class="sidebar">
      <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">x</a>
  '

  while read -r num; do
    local name="${menuitems[$num]}"
    echo '    <a href="javascript:void(0)" onclick="jump('"'$num'"')">'"$name"'</a>'

  done < <(
    tr ' ' '\n' <<< "${!menuitems[@]}" | sort -n
  )
  echo '
    </div>"
  '
}

print_table() {

  echo '<div id="grid">'

  for image in *.jpg; do
    print_image "$image"
  done

  echo '</div>'
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
      local name; name="$( $sha "$image" | awk '{print $1}' )"

      [[ -f "$imgbase"/"$name" ]] || {
        {
          convert \
            -resize 400 \
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
    <title>Diving Pictures</title>
  </head>
  '
}

print_scripts() {

  echo '
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="jquery.min.js"></script>
    <link rel="stylesheet" href="jquery.fancybox.min.css"/>
    <script src="jquery.fancybox.min.js"></script>
  '
}

print_style() {

echo '
  <style>

#grid {
  display: grid;
  grid-template-columns: repeat( auto-fit, minmax(300px, max-content));
  justify-content: center;
  grid-grap: 1rem;
}

img {
  width: 300px;
  padding: 5px;
}

body {
  background-color: black;
  text-align:       center;
}

figcaption, h1, h4 {
  color: white;
}

.sidebar {
  height: 100%;
  width: 0;
  position: fixed;
  z-index: 1;
  top: 0;
  left: 0;
  background-color: #111;
  overflow-x: hidden;
  transition: 0.5s;
  padding-top: 60px;
}

.sidebar a {
  padding: 8px 8px 8px 32px;
  text-decoration: none;
  font-size: 25px;
  color: #818181;
  display: block;
  transition: 0.3s;
}

.sidebar a:hover {
  color: #f1f1f1;
}

.sidebar .closebtn {
  position: absolute;
  top: 0;
  right: 25px;
  font-size: 36px;
  margin-left: 50px;
}

.openbtn {
  float: right;
  position: fixed;
  right: 25px;
  font-size: 20px;
  cursor: pointer;
  background-color: #111;
  color: white;
  padding: 10px 15px;
  border: none;
}

.openbtn:hover {
  background-color: #444;
}
  </style>
'
}

javascript() {

  local first="${dives[0]}"
  local second="${dives[1]}"

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

    // preload two groups to fill the screen
    $("#0").load("'"$first"'").addClass("isloaded");
    $("#1").load("'"$second"'").addClass("isloaded");

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
declare -A menuitems
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
  print_style

  echo '  <body>'
  print_scripts
  echo '    <button class="openbtn" onclick="openNav()">Menu</button>'

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
    mv tmp.html "$htmlhash".html

    menuitems[$counter]="$( basename "$f" )"
    (( counter++ ))

    (( DEBUG )) && echo >&2
    (( DEBUG )) && echo >&2
  done < <(
    for z in "$target"/*; do
      echo "$z"
    done | $tac
  )

  print_menu
  echo '  </body>'

  javascript
  echo '</html>'
}

main "$@" > index.html
