#!/usr/bin/python3

'''
Python implementation of runner.sh
'''

import os
import operator
from typing import Callable

import hypertext
from hypertext import Where
from util import collection
from util.image import Image
import util.common as utility


_html_head = '''\
<!DOCTYPE html>
<html>
  <head>
    <title>Diving Timeline</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Scuba diving pictures organized into a timeline and by location">
    <link rel="stylesheet" href="/style.css"/>
  </head>
'''

_html_switcher = '''\
    <a href="/taxonomy/index.html">
        <h2 class="top switch taxonomy">Taxonomy</h2>
    </a>
    <div class="top buffer"></div>
    <a href="/timeline/index.html">
        <h1 class="top switch">Timeline</h1>
    </a>
    <div class="top buffer"></div>
    <a href="/gallery/index.html">
        <h2 class="top switch gallery">Gallery</h2>
    </a>
'''

_html_scripts = '''\
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
    <script src="/jquery.fancybox.min.js"></script>
    <script>
    function flip(elem) {
        const label = "is-flipped";
        if (elem.classList.contains(label)) {
            elem.classList.remove(label);
        } else {
            const seconds = 10;
            elem.classList.add(label);
            setTimeout(function () {
                if (elem.classList.contains(label)) {
                    elem.classList.remove(label);
                }
            }, 1000 * seconds);
        }
    }
    </script>
'''


def timeline(imagef: Callable[[str, str], Image]):
    '''generate all the timeline html'''
    dives = [
        d
        for d in sorted(os.listdir(utility.root), reverse=True)
        if d.startswith('20')
    ]
    results = []

    for dive in dives:
        results.append(_subpage(dive, imagef))

    paths = [path for (path, _) in results]
    divs = '\n'.join(f"    <div id='{i}'></div>" for i, _ in enumerate(dives))

    html = '\n'.join(
        [
            _html_head,
            '  <body>',
            _html_switcher,
            _html_scripts,
            divs,
            _javascript(paths),
            '  </body>',
            '</html>',
        ]
    )

    results.append(('index.html', html))
    return results


def _image_html(image):
    '''build the html for a picture'''
    thumbnail = image.thumbnail()
    fullsize = image.fullsize()
    subject = image.name

    name_html = hypertext.image_to_name_html(image, Where.Sites)
    site_html = hypertext.image_to_site_html(image, Where.Sites)

    return f'''
  <div class="card" onclick="flip(this);">
    <div class="card_face card_face-front">
      <img width=300 alt="{subject}" loading="lazy" src="{thumbnail}">
    </div>
    <div class="card_face card_face-back">
      {name_html}
      {site_html}
      <a class="top elem timeline" data-fancybox="gallery" data-caption="{subject}" href="{fullsize}">
      Fullsize Image
      </a>
      <p class="top elem">Close</p>
    </div>
  </div>
'''


def _subpage(dive, imagef: Callable[[str, str], Image]):
    '''build the sub page for this dive'''
    when, title = dive.split(' ', 1)

    while title[0].isdigit():
        title = title[1:]

    html = f'''\
<h1>{title}</h1>
<h4>{when}</h4>
<div class="grid">
'''

    images = sorted(
        collection.delve(dive, imagef), key=operator.attrgetter('number')
    )
    html += '\n'.join(_image_html(image) for image in images)

    html += '''\
</div>
'''

    path = utility.sanitize_link(dive) + '.html'
    return path, html


def _javascript(paths):
    '''build the javascript lazy loader'''
    html = '''\
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
    '''

    # preload
    first, second, third = paths[:3]
    html += f'''
    $("#0").load("{first}" ).addClass("isloaded");
    $("#1").load("{second}").addClass("isloaded");
    $("#2").load("{third}" ).addClass("isloaded");
    '''

    # scroll function
    html += '''
    $(window).scroll(function() {
'''
    html += '\n'.join(
        f'      if (loader("#{i}", "{path}")) {{ return }};'
        for i, path in enumerate(paths)
        if i > 2
    )

    html += '''\
    });
  </script>'
    '''
    return html
