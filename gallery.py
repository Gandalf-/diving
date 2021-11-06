#!/usr/bin/python3

'''
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
'''

import enum
import re
import os
import sys
import multiprocessing
from datetime import datetime

import information
import taxonomy
import collection
from detective import javascript as game

from image import (
    categorize,
    uncategorize,
    split,
    Image,
)
import static
from utility import tree_size


# pylint: disable=too-many-locals
# pylint: disable=line-too-long

Where = enum.Enum('Where', 'Gallery Taxonomy')


def find_by_path(tree, needle):
    """search the tree for an image with this path"""
    if not isinstance(tree, dict):
        for image in tree:
            if needle in image.path():
                return image
    else:
        for child in tree.values():
            found = find_by_path(child, needle)
            if found:
                return found

    return None


def find_representative(tree, lineage=None):
    """grab one image to represent this tree"""
    if not lineage:
        lineage = []

    # forwards for gallery
    category = ' '.join(lineage)
    if category in static.pinned:
        found = find_by_path(tree, static.pinned[category])
        if found:
            return found

    # backwards for taxonomy
    category = ' '.join(lineage[::-1])
    if category in static.pinned:
        found = find_by_path(tree, static.pinned[category])
        if found:
            return found

    if not isinstance(tree, dict):
        results = tree
    else:
        results = (
            find_representative(values, lineage=[key] + lineage)
            for (key, values) in tree.items()
        )

    def get_path(image):
        assert isinstance(image, Image), image
        return image.path()

    results = sorted(results, key=get_path, reverse=True)
    assert results, (tree, lineage)
    return results[0]


def lineage_to_link(lineage, side, key=None):
    """get a link to this page"""
    if not lineage:
        name = key
    else:
        name = ' '.join(lineage)

        if key and side == 'left':
            name = key + ' ' + name

        if key and side == 'right':
            name = name + ' ' + key

    return name.replace(' ', '-')


def html_head(title):
    """top of the document"""
    if title.endswith('Gallery'):
        desc = (
            'Scuba diving pictures organized into a tree structure by '
            'subject\'s common names. Such as anemone, fish, '
            'nudibranch, octopus, sponge.'
        )
    elif title.endswith('Taxonomy'):
        desc = (
            'Scuba diving pictures organized into a tree structure by '
            'subject\'s scientific classification. Such as Athropoda, '
            'Cnidaria, Mollusca.'
        )
    else:
        desc = f'Scuba diving pictures related to {title}'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <title>{title}</title>
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


def html_top_title(where):
    """html top for top level pages"""
    title = f"{where.title()}"

    display = uncategorize(title)
    if where == 'gallery':
        display = display.title()

    timeline = '''
        <a href="/timeline/index.html">
            <h1 class="top switch">Timeline</h1>
        </a>
    '''
    gallery = '''
        <a href="/gallery/index.html">
            <h1 class="top switch gallery">Gallery</h1>
        </a>
    '''
    _taxonomy = '''
        <a href="/taxonomy/index.html">
            <h1 class="top switch taxonomy">Taxonomy</h1>
        </a>
    '''
    detective = '''
        <a href="/detective/index.html">
            <h1 class="top switch detective">Detective</h1>
        </a>
    '''
    spacer = '<div class="top" id="buffer"></div>\n'

    html = html_head(display)
    if where == 'gallery':
        parts = [
            timeline.replace('h1', 'h2'),
            gallery,
            detective.replace('h1', 'h2'),
        ]
    else:
        parts = [
            detective.replace('h1', 'h2'),
            _taxonomy,
            timeline.replace('h1', 'h2'),
        ]

    html += spacer.join(parts)
    html += '''
        <p class="scientific"></p>
    </div>
    '''

    return html, title


def html_taxonomy_title(lineage, scientific):
    """html head and title section"""
    assert lineage

    title = ' '.join(lineage)
    display = uncategorize(title)
    side = 'right'

    html = html_head(display)
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

    return html, title


def html_title(lineage, where, scientific):
    """html head and title section"""
    if not lineage:
        return html_top_title(where)

    if where == 'taxonomy':
        return html_taxonomy_title(lineage, scientific)

    title = ' '.join(lineage)
    display = uncategorize(title).title()
    side = 'left'
    html = html_head(display)

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

    return html, title


def get_info(where, lineage):
    """wikipedia information if available"""
    if where == 'gallery':
        return ''

    htmls = []
    seen = set()

    for part in information.lineage_to_names(lineage):
        html, url = information.html(part)

        if url in seen:
            continue
        seen.add(url)

        htmls.append(html)

    return '<br>'.join(htmls)


def html_tree(tree, where, scientific, lineage=None):
    """html version of display"""
    if not lineage:
        lineage = []

    side = 'left' if where == 'gallery' else 'right'

    html, title = html_title(lineage, where, scientific)
    results = []

    has_subcategories = [1 for key in tree.keys() if key != "data"] != []
    if has_subcategories:
        html += '<div class="grid">'

    # categories
    for key, value in sorted(tree.items()):
        if key == "data":
            continue

        new_lineage = [key] + lineage if side == 'left' else lineage + [key]
        size = tree_size(value)
        example = find_representative(value, [key] + lineage)

        if where == 'gallery':
            subject = key.title()
        else:
            subject = taxonomy.simplify(key)

        html += """
        <div class="image">
        <a href="{link}">
            <img width=300 loading="lazy" src="/imgs/{thumbnail}">
            <h3>
              <span class="sneaky">{size}</span>
              {subject}
              <span class="count">{size}</span>
            </h3>
        </a>
        </div>
        """.format(
            subject=subject,
            link="/{where}/{path}.html".format(
                where=where, path=lineage_to_link(lineage, side, key),
            ),
            thumbnail=example.thumbnail(),
            size='{}:{}'.format(
                sum(1 for k in value if k != 'data') or '', size
            ),
        )

        results.extend(
            html_tree(value, where, scientific, lineage=new_lineage)
        )

    if has_subcategories:
        html += "</div>"

    direct = tree.get("data", [])
    direct = sorted(direct, key=lambda x: x.path(), reverse=True)
    assert not (direct and has_subcategories)

    # direct examples
    if direct:
        seen = set()
        html += '<div class="grid">'

        for image in direct:
            identifier = tuple([image.name, image.path()])
            if identifier in seen:
                continue

            html += """
            <a data-fancybox="gallery" data-caption="{name}" href="{fullsize}">
              <img width=300 loading="lazy" src="/imgs/{thumbnail}">
            </a>
            """.format(
                name='{} - {}'.format(image.name, image.location()),
                fullsize=image.fullsize(),
                thumbnail=image.thumbnail(),
            )

            seen.add(identifier)
        html += "</div>"

    # wikipedia info
    info = get_info(where, lineage)
    now = datetime.now()

    html += f"""
      {info}
      </div>
      <footer>
        <p>Copyright austin@anardil.net {now.year}</p>
      </footer>
      {html_scripts}
    </body>
    </html>
    """

    if title in ('Gallery', 'Taxonomy'):
        title = 'index'

    results.append((title, html))
    return results


def names_pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "gallery/{name}.html".format(name=title.replace(" ", "-"))

    with open(path, "w+") as f:
        print(html, file=f)


def taxia_pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "taxonomy/{name}.html".format(name=title.replace(" ", "-"))

    with open(path, "w+") as f:
        print(html, file=f)


def write_all_html():
    ''' main '''
    pool = multiprocessing.Pool()

    print("loading data... ", end="", flush=True)
    tree = collection.go()
    scientific = taxonomy.mapping()
    taxia = taxonomy.gallery_tree(tree)
    print("done", tree_size(tree), "images loaded")

    print("walking name tree... ", end="", flush=True)
    name_htmls = html_tree(tree, "gallery", scientific)
    print("done", len(name_htmls), "pages prepared")

    print("walking taxia tree... ", end="", flush=True)
    scientific = {v.replace(' sp', ''): k for k, v in scientific.items()}
    taxia_htmls = html_tree(taxia, "taxonomy", scientific)
    print("done", len(taxia_htmls), "pages prepared")

    print("writing html... ", end="", flush=True)
    pool.map(names_pool_writer, name_htmls)
    pool.map(taxia_pool_writer, taxia_htmls)
    print("done")

    print("writing game... ", end="", flush=True)
    game(False)
    print("done")


def _find_links():
    """check the html directory for internal links"""

    def extract_from(fd):
        """get links from a file"""
        for line in fd:
            if 'href' not in line:
                continue

            for link in re.findall(r'href=\"(.+?)\"', line):
                if link.startswith('http'):
                    continue

                link = link[1:]
                yield path, link

    for directory in ('taxonomy', 'gallery'):
        for filename in os.listdir(directory):
            if not filename.endswith(".html"):
                continue

            path = os.path.join(directory, filename)
            with open(path) as fd:
                yield from extract_from(fd)


# INFORMATIONAL

def link_check():
    """check the html directory for broken links by extracting all the
    internal links from the written files and looking for those as paths
    """
    for path, link in _find_links():
        if not os.path.exists(link):
            print('broken', link, 'in', path)


# resources

html_scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery-3.6.0.min.js"></script>
    <script src="/jquery.fancybox.min.js"></script>
"""


if not sys.flags.interactive and __name__ == "__main__":
    if len(sys.argv) == 2:
        root = sys.argv[1]

    write_all_html()
    link_check()
