#!/usr/bin/python3

'''
html generation
'''

import os
import enum
import datetime

import locations

from util.collection import expand_names
from util.common import strip_date, fast_exists, titlecase, sanitize_link
from util.image import (
    categorize,
    uncategorize,
    split,
)
from util import taxonomy


Where = enum.Enum('Where', 'Gallery Taxonomy Sites')
Side = enum.Enum('Side', 'Left Right')

scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery-3.6.0.min.js"></script>
    <script src="/jquery.fancybox.min.js"></script>
    <script>
    function flip(elem) {
        const label = 'is-flipped';
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
"""


def title(lineage, where, scientific):
    """html head and title section"""
    if not lineage:
        return _top_title(where)

    if where == Where.Taxonomy:
        return _taxonomy_title(lineage, scientific)

    if where == Where.Gallery:
        return _gallery_title(lineage, scientific)

    if where == Where.Sites:
        return _sites_title(lineage)

    return '', ''


def lineage_to_link(lineage, side, key=None):
    """get a link to this page"""
    if not lineage:
        name = key
    else:
        name = ' '.join(lineage)

        if key and side == Side.Left:
            name = key + ' ' + name

        if key and side == Side.Right:
            name = name + ' ' + key

    return sanitize_link(name)


def _image_to_gallery_link(image):
    """get the /gallery link

    there could be mulitple subjects in this image, just take the first for now
    """
    first = next(expand_names([image]))
    name = sanitize_link(first.normalized())
    url = f'gallery/{name}.html'

    if fast_exists(url):
        return f'/{url}'

    return None


def _image_to_sites_link(image):
    """get the /sites/ link"""
    when, where = image.location().split(' ', 1)
    site = locations.add_context(where)
    link = sanitize_link(site)
    url = f'sites/{link}-{when}.html'

    if fast_exists(url):
        return f'/{url}'

    return None


# PRIVATE


def _head(_title):
    """top of the document"""
    if _title.endswith('Gallery'):
        desc = (
            'Scuba diving pictures organized into a tree structure by '
            'subject\'s common names. Such as anemone, fish, '
            'nudibranch, octopus, sponge.'
        )
    elif _title.endswith('Taxonomy'):
        desc = (
            'Scuba diving pictures organized into a tree structure by '
            'subject\'s scientific classification. Such as Arthropoda, '
            'Cnidaria, Mollusca.'
        )
    elif _title.endswith('Sites'):
        desc = (
            'Scuba diving pictures from Bonaire, Galapagos, British Columbia, '
            'and Washington organized into a tree structure by dive site.'
        )
    else:
        _title = strip_date(_title)
        desc = f'Scuba diving pictures related to {_title}'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <title>{_title}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name=description content="{desc}">
        <link rel="stylesheet" href="/style.css"/>
        <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
      </head>

      <body>
      <div class="wrapper">
      <div class="title">
    """


def _gallery_title(lineage, scientific):
    '''html head and title section for gallery pages'''
    assert lineage
    side = Side.Left

    # check for scientific name for gallery
    slink = sname = taxonomy.gallery_scientific(lineage, scientific)
    sname = taxonomy.simplify(sname)
    if slink.endswith(' sp.'):
        slink = slink.replace(' sp.', '')

    scientific_common_name = slink.lower().endswith(lineage[0].lower())

    if scientific_common_name:
        lineage = [slink[-len(lineage[0]) :]] + [
            titlecase(e) for e in lineage[1:]
        ]
    else:
        lineage = [titlecase(e) for e in lineage]

    _title = ' '.join(lineage)
    display = uncategorize(_title)

    slink = sanitize_link(slink)
    html = _head(display)

    # create the buttons for each part of our name lineage
    for i, name in enumerate(lineage):
        if i == 0 and scientific_common_name:
            name = f'<em>{name}</em>'

        partial = lineage[i:]
        _link = f'/gallery/{lineage_to_link(partial, side)}.html'.lower()

        html += f"""
        <a href="{_link}">
            <h1 class="top">{name}</h1>
        </a>
        """

    html += """
        <div class="top buffer"></div>

        <a href="/gallery/index.html">
            <h1 class="top switch gallery">Gallery</h1>
        </a>
    """

    if slink:
        html += f"""
        <a href="/taxonomy/{slink}.html" class="scientific crosslink">{sname}</a>
        </div>
        """
    else:
        html += f"""
        <p class="scientific">{sname}</p>
        </div>
        """

    return html, _title.lower()


def _taxonomy_title(lineage, scientific):
    '''html head and title section for taxonomy pages'''
    assert lineage

    _title = ' '.join(lineage)
    side = Side.Right

    html = _head(' '.join(lineage[-2:]))
    html += """
        <a href="/taxonomy/index.html">
            <h1 class="top switch taxonomy">Taxonomy</h1>
        </a>
        <div class="top buffer"></div>
    """

    # create the buttons for each part of our name lineage
    for i, name in enumerate(lineage):

        name = taxonomy.simplify(name)
        partial = lineage[: i + 1]
        link = f"/taxonomy/{lineage_to_link(partial, side)}.html"

        html += f"""
        <a href="{link}">
            <h1 class="top">{name}</h1>
        </a>
        """

    # check for common name for taxonomy
    name = ""
    history = ' '.join(lineage).split(' ')

    while history and not name:
        name = scientific.get(' '.join(history)) or ""
        history = history[:-1]

    name = titlecase(name)
    link = split(categorize(name.lower()))
    link = sanitize_link(link)

    if link:
        html += f"""
        <a href="/gallery/{link}.html" class="scientific crosslink">{name}</a>
        </div>
        """
    else:
        html += f"""
        <p class="scientific">{name}</p>
        </div>
        """

    return html, _title


def _sites_title(lineage):
    '''html head and title section for sites pages'''
    assert lineage

    display = _title = ' '.join(lineage)
    side = Side.Right

    html = _head(display)
    html += """
        <a href="/sites/index.html">
            <h1 class="top switch sites">Sites</h1>
        </a>
        <div class="top buffer"></div>
    """

    # create the buttons for each part of our name lineage
    name = ""
    try:
        last = lineage[-1]
        if ' ' in last:
            *rest, last = last.split(' ')
            rest = ' '.join(rest)
        else:
            rest = None

        d = datetime.datetime.strptime(last, '%Y-%m-%d')
        assert d

        name = last
        if rest:
            lineage = lineage[:-1] + [rest]
    except ValueError:
        pass

    for i, _name in enumerate(lineage):
        partial = lineage[: i + 1]
        link = f"/sites/{lineage_to_link(partial, side)}.html"

        # it's possible that this is the only date available for this location,
        # in which case we want the name to include the location and trim the
        # lineage on more value
        if not os.path.exists(link[1:]):
            name = _name + ' ' + name
            continue

        html += f"""
        <a href="{link}">
            <h1 class="top">{_name}</h1>
        </a>
        """

    # ???
    html += f"""
    <p class="scientific">{name}</p>
    </div>
    """

    return html, _title


def image_to_name_html(image, where):
    '''create the html gallery link, entry, or nothing for this image'''
    if where in (Where.Gallery, Where.Taxonomy):
        return ''

    name_url = _image_to_gallery_link(image)
    if name_url:
        name_html = (
            f'<a class="top elem gallery" href="{name_url}">{image.name}</a>'
        )
    else:
        name_html = f'<p class="top elem nolink">{image.name}</p>'

    return name_html


def image_to_site_html(image, where):
    '''create the html site link, entry, or nothing for this image'''
    if where == Where.Sites:
        return ''

    site_url = _image_to_sites_link(image)
    if site_url:
        site_html = (
            f'<a class="top elem sites" href="{site_url}">{image.site()}</a>'
        )
    else:
        site_html = f'<p class="top elem nolink">{image.site()}</p>'

    return site_html


def _top_title(where):
    """html top for top level pages"""
    # title = 'Gallery' if where == Where.Gallery else 'Taxonomy'
    _title = titlecase(where.name)

    display = uncategorize(_title)
    if where == Where.Gallery:
        display = titlecase(display)

    _timeline = '''
        <a href="/timeline/index.html">
            <h1 class="top switch">Timeline</h1>
        </a>
    '''
    _gallery = '''
        <a href="/gallery/index.html">
            <h1 class="top switch gallery">Gallery</h1>
        </a>
    '''
    _taxonomy = '''
        <a href="/taxonomy/index.html">
            <h1 class="top switch taxonomy">Taxonomy</h1>
        </a>
    '''
    _detective = '''
        <a href="/detective/index.html">
            <h1 class="top switch detective">Detective</h1>
        </a>
    '''
    _sites = '''
        <a href="/sites/index.html">
            <h1 class="top switch sites">Sites</h1>
        </a>
    '''
    spacer = '<div class="top buffer"></div>\n'

    html = _head(display)
    if where == Where.Gallery:
        parts = [
            _timeline.replace('h1', 'h2'),
            _gallery,
            _detective.replace('h1', 'h2'),
        ]
    elif where == Where.Taxonomy:
        parts = [
            _sites.replace('h1', 'h2'),
            _taxonomy,
            _timeline.replace('h1', 'h2'),
        ]
    elif where == Where.Sites:
        parts = [
            _detective.replace('h1', 'h2'),
            _sites,
            _taxonomy.replace('h1', 'h2'),
        ]

    html += spacer.join(parts)
    html += '''
        <p class="scientific"></p>
    </div>
    '''

    return html, _title
