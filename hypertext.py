#!/usr/bin/python3

'''
html generation
'''

import enum
import datetime

import taxonomy
from image import (
    categorize,
    uncategorize,
    split,
)
from utility import strip_date


Where = enum.Enum('Where', 'Gallery Taxonomy Sites')
Side = enum.Enum('Side', 'Left Right')

scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery-3.6.0.min.js"></script>
    <script src="/jquery.fancybox.min.js"></script>
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

    return name.replace(' ', '-').replace("'", '')


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
    ''' html head and title section for gallery pages
    '''
    assert lineage

    _title = ' '.join(lineage)
    display = uncategorize(_title).title()
    side = Side.Left
    html = _head(display)

    # create the buttons for each part of our name lineage
    for i, name in enumerate(lineage):

        partial = lineage[i:]
        link = "/gallery/{path}.html".format(
            path=lineage_to_link(partial, side)
        )

        html += """
        <a href="{link}">
            <h1 class="{classes}">{title}</h1>
        </a>
        """.format(
            title=name.title(), classes="top", link=link,
        )

    html += """
        <div class="top" id="buffer"></div>

        <a href="/gallery/index.html">
            <h1 class="top switch gallery">Gallery</h1>
        </a>
    """

    # check for scientific name for gallery
    link = name = taxonomy.gallery_scientific(lineage, scientific)
    name = taxonomy.simplify(name)
    if link.endswith(' sp'):
        link = link.replace(' sp', '')
    link = link.replace(' ', '-')

    if link:
        html += f"""
        <a href="/taxonomy/{link}.html" class="scientific crosslink">{name}</a>
        </div>
        """
    else:
        html += f"""
        <p class="scientific">{name}</p>
        </div>
        """

    return html, _title


def _taxonomy_title(lineage, scientific):
    ''' html head and title section for taxonomy pages
    '''
    assert lineage

    _title = ' '.join(lineage)
    display = uncategorize(_title)
    side = Side.Right

    html = _head(display)
    html += """
        <a href="/taxonomy/index.html">
            <h1 class="top switch taxonomy">Taxonomy</h1>
        </a>
        <div class="top" id="buffer"></div>
    """

    # create the buttons for each part of our name lineage
    for i, name in enumerate(lineage):

        name = taxonomy.simplify(name)
        partial = lineage[: i + 1]
        link = "/taxonomy/{path}.html".format(
            path=lineage_to_link(partial, side)
        )

        html += """
        <a href="{link}">
            <h1 class="{classes}">{title}</h1>
        </a>
        """.format(
            title=name, classes="top", link=link,
        )

    # check for common name for taxonomy
    name = ""
    history = ' '.join(lineage).split(' ')

    while history and not name:
        name = scientific.get(' '.join(history)) or ""
        history = history[:-1]

    name = name.title()
    link = split(categorize(name.lower()))
    link = link.replace(' ', '-')

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
    ''' html head and title section for sites pages
    '''
    assert lineage

    display = _title = ' '.join(lineage)
    side = Side.Right

    html = _head(display)
    html += """
        <a href="/sites/index.html">
            <h1 class="top switch sites">Sites</h1>
        </a>
        <div class="top" id="buffer"></div>
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
        assert d or True  # pylint please

        name = last
        if rest:
            lineage = lineage[:-1] + [rest]
    except ValueError:
        pass

    for i, _name in enumerate(lineage):
        partial = lineage[: i + 1]
        link = "/sites/{path}.html".format(
            path=lineage_to_link(partial, side)
        )

        html += """
        <a href="{link}">
            <h1 class="{classes}">{title}</h1>
        </a>
        """.format(
            title=_name, classes="top", link=link,
        )

    # ???
    html += f"""
    <p class="scientific">{name}</p>
    </div>
    """

    return html, _title


def _top_title(where):
    """html top for top level pages"""
    # title = 'Gallery' if where == Where.Gallery else 'Taxonomy'
    _title = where.name.title()

    display = uncategorize(_title)
    if where == Where.Gallery:
        display = display.title()

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
    spacer = '<div class="top" id="buffer"></div>\n'

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
