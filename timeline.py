#!/usr/bin/python3

"""
Python implementation of runner.sh
"""

import operator
import os
from typing import Any, Dict, List, Tuple

import hypertext
import locations
from hypertext import Where
from util import collection, common, log, static


def timeline() -> List[Tuple[str, str]]:
    """generate all the timeline html"""
    dives = [d for d in sorted(os.listdir(static.image_root), reverse=True) if d.startswith('20')]
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

    results.append(('timeline/index.html', html))
    return results


def _subpage(dive: str) -> Tuple[str, str]:
    """build the sub page for this dive"""
    when, title = dive.split(' ', 1)

    while title[0].isdigit() or title[0] == ' ':
        title = title[1:]

    sites_link = locations.sites_link(when, title)
    when = common.pretty_date(when)

    region = locations.get_region(title)
    if sites_link:
        name = f"""\
<a href="{sites_link}">
    <h2 class="where sites pad-down">{title}</h2>
</a>
"""
    else:
        name = f"""\
    <h2 class="tight">{title}</h2>
"""

    html = f"""\
{name}
<h3 class="tight">{when} - {region}</h3>
"""
    info = log.lookup(dive)
    if info:
        html += log.dive_info_html(info)

    html += """\
<div class="grid">
"""

    path = os.path.join(static.image_root, dive)
    images = sorted(collection.delve(path), key=operator.attrgetter('number'))
    html += '\n'.join(hypertext.html_direct_image(image, Where.Sites, True) for image in images)

    html += """\
</div>
"""

    path = common.sanitize_link(dive) + '.html'
    return f'timeline/{path}', html


def _javascript(paths: List[str]) -> str:
    """build the javascript lazy loader"""
    html = """\
  <script>
    var furthest = 0;

    function loader(elem, content) {
      const top_of_elem = $(elem).offset().top;
      const bot_of_elem = top_of_elem + $(elem).outerHeight();
      const bot_of_scrn = $(window).scrollTop() + window.innerHeight;
      const top_of_scrn = $(window).scrollTop();

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

      $(elem).load(content, function() {
          $(elem).addClass("isloaded");
          enableAutoPlay();
      });

      return true;
    }
    // preload three groups to fill the screen
    """

    # preload
    first, second, third = paths[:3]
    html += f"""
    $("#0").load("/{first}", function () {{
        $("#0").addClass("isloaded");
        enableAutoPlay();
    }});
    $("#1").load("/{second}", function () {{
        $("#1").addClass("isloaded");
        enableAutoPlay();
    }});
    $("#2").load("/{third}", function () {{
        $("#2").addClass("isloaded");
        enableAutoPlay();
    }});
    """

    # scroll function
    html += """
    $(window).scroll(function() {
"""
    html += '\n'.join(
        f'      if (loader("#{i}", "/{path}")) {{ return }};'
        for i, path in enumerate(paths)
        if i > 2
    )

    html += """
    });
  </script>
    """
    return html
