#!/usr/bin/python3

'''
Python implementation of runner.sh
'''

import os
import operator
from typing import List, Tuple, Dict, Any

import hypertext
import locations
from hypertext import Where
from util import collection
from util.image import Image
import util.common as utility


_html_switcher = '''\
    <div class="title">
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
    </div>
'''


def timeline() -> List[Tuple[str, str]]:
    '''generate all the timeline html'''
    dives = [
        d
        for d in sorted(os.listdir(utility.root), reverse=True)
        if d.startswith('20')
    ]
    results = []

    for dive in dives:
        results.append(_subpage(dive))

    paths = [path for (path, _) in results]
    divs = '\n'.join(f"    <div id='{i}'></div>" for i, _ in enumerate(dives))

    fake_scientific: Dict[str, Any] = {}
    title, _ = hypertext.title([], Where.Timeline, fake_scientific)

    html = '\n'.join(
        [
            title,
            divs,
            '</div>',
            hypertext.scripts,
            _javascript(paths),
            '  </body>',
            '</html>',
        ]
    )

    results.append(('index.html', html))
    return results


def _image_html(image: Image) -> str:
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


def _subpage(dive: str) -> Tuple[str, str]:
    '''build the sub page for this dive'''
    when, title = dive.split(' ', 1)

    while title[0].isdigit() or title[0] == ' ':
        title = title[1:]

    sites_link = locations.sites_link(when, title)
    when = utility.pretty_date(when)

    location = locations.get_context(title)
    if not location and title.startswith('Bonaire'):
        _, title = title.split('Bonaire ')
        location = 'Bonaire'

    assert location, f'{dive} has no location'
    if sites_link:
        name = f'''\
<a href="{sites_link}">
    <h1 class="where sites">{title}</h1>
</a>
'''
    else:
        name = f'''\
    <h1>{title}</h1>
'''

    html = f'''\
{name}
<h3>{when} - {location}</h3>
<div class="grid">
'''

    images = sorted(collection.delve(dive), key=operator.attrgetter('number'))
    html += '\n'.join(_image_html(image) for image in images)

    html += '''\
</div>
'''

    path = utility.sanitize_link(dive) + '.html'
    return path, html


def _javascript(paths: List[str]) -> str:
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
  </script>
    '''
    return html
