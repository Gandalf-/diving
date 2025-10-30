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

    fake_scientific: Dict[str, Any] = {}
    title, _ = hypertext.title([], Where.Timeline, fake_scientific)
    paths = [f'/{path}' for (path, _) in results]

    with open(static.timeline_js_path) as fd:
        timeline_js = fd.read()

    html = '\n'.join(
        [
            title,
            '</div>',
            hypertext.scripts,
            '  <script>',
            f'const timelineUrls = {paths};',
            timeline_js,
            '  </script>',
            '  </body>',
            '</html>',
        ]
    )

    results.append(('timeline/index.html', html))
    return results


def _subpage(dive: str) -> Tuple[str, str]:
    """build the sub page for this dive"""
    when, title = dive.split(' ', 1)

    while title and (title[0].isdigit() or title[0] == ' '):
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
