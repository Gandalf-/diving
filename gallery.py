#!/usr/bin/python3

'''
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
'''

import sys
import multiprocessing

import taxonomy
import collection

from image import uncategorize, splits
from utility import tree_size


# pylint: disable=too-many-locals
# pylint: disable=line-too-long


def tree_print(tree, lineage="", depth=0):
    ''' print the tree to stdout '''

    for key, value in sorted(tree.items()):
        if key == "data":
            print(" " * depth, len(tree["data"]), "direct pictures")
            continue

        child = key + " " + lineage if lineage else key
        print(" " * depth, child)
        tree_print(value, lineage=child, depth=depth + 2)


pinned = {
    "crab": '2020-06-17 Rockaway Beach/005 - Dungeness Crab.jpg',
    "anemone": '2019-11-12 Rockaway Beach/019 - Anemones.jpg',
    'barnacle': '2019-12-30 Metridium/005 - Giant Acorn Barnacle.jpg',
    'diver': '2019-10-31 Klein Bonaire M/017 - Divers.jpg',
    'eel': '2020-07-26 Port Townsend/056 - Juvenile Wolf Eel.jpg',
    'fish': '2020-03-01 Power Lines/017 - Juvenile Yellow Eye Rockfish',
    # 'nudibranch': '2020-07-09 Rockaway Beach/005 - Alabaster Nudibranch.jpg',
    'nudibranch': (
        '2020-09-08 Sund Rock South Wall/'
        '034 - Red Flabellina Nudibranchs.jpg'
    ),
    'lobster': '2020-02-19 Sund Rock South Wall/033 - Squat Lobster.jpg',
}


def find_by_path(tree, needle):
    ''' search the tree for an image with this path
    '''
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
    """ grab one image to represent this tree
    """
    if not lineage:
        lineage = []

    category = ' '.join(lineage)
    if category in pinned:
        found = find_by_path(tree, pinned[category])
        if found:
            return found

    if not isinstance(tree, dict):
        results = tree
    else:
        results = (
            find_representative(values, lineage=[key] + lineage)
            for (key, values) in tree.items()
        )

    results = sorted(results, key=lambda x: x.path(), reverse=True)
    return results[0]


def html_title(lineage, scientific):
    ''' html head and title section
    '''
    title = " ".join(lineage) or "Diving Gallery"
    display = uncategorize(title).title()

    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>{title}</title>
        <link rel="stylesheet" href="/style.css"/>
        <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
      </head>

      <body>
      {scripts}
      <div class="title">
    """.format(
        title=display, scripts=html_scripts
    )

    # create the buttons for each part of our name lineage
    for i, parent in enumerate(lineage):
        link = "/gallery/" + " ".join(lineage[i:]) + ".html"
        link = link.replace(" ", "-")

        last = i == len(lineage) - 1

        html += """
        <a href="{link}">
            <h1 class="{classes}">{title}</h1>
        </a>
        """.format(
            title=parent.title(),
            classes="top" + (" last" if last else ""),
            link=link,
        )

    # only include link to timeline on the top level page
    if not lineage:
        html += """
        <a href="/timeline/index.html">
            <h1 class="top switch">Diving Timeline</h1>
        </a>
        <div class="top" id="buffer"></div>
        """

    # always have a link to the top level of the gallery
    html += """
    <a href="/gallery/index.html">
        <h1 class="top switch">Diving Gallery</h1>
    </a>
    """

    # check for scientific name
    if lineage and lineage[-1] == 'egg':
        lineage = lineage[:-1]

    def lookup(names):
        candidate = uncategorize(' '.join(names).lower())
        if 'rock fish' in candidate:
            candidate = candidate.replace('rock fish', 'rockfish')
        return scientific.get(candidate)

    name = lookup(lineage)

    # drop the first word
    if not name:
        name = lookup(lineage[1:])

    # drop the first two words
    if not name:
        name = lookup(lineage[2:])

    if not name:
        print(' '.join(lineage))
    name = name or ""

    html += f"""
    <p class="scientific">{name}</p>
    </div>
    """

    return html, title


def html_tree(tree, scientific, lineage=None):
    """ html version of display
    """
    if not lineage:
        lineage = []

    html, title = html_title(lineage, scientific)
    results = []

    has_subcategories = [1 for key in tree.keys() if key != "data"] != []
    if has_subcategories:
        html += '<div class="grid">'

    # categories
    for key, value in sorted(tree.items()):
        if key == "data":
            continue

        child = key + " " + " ".join(lineage) if lineage else key
        size = tree_size(value)

        example = find_representative(value, [key] + lineage)
        html += """
        <div class="image">
        <a href="{link}">
            <img src="/imgs/{thumbnail}" alt="">
            <h3>
              <span class="sneaky">{size}</span>
              {subject}
              <span class="count">{size}</span>
            </h3>
        </a>
        </div>
        """.format(
            subject=key.title(),
            link="/gallery/{path}.html".format(path=child.replace(" ", "-")),
            thumbnail=example.hash(),
            size='{}:{}'.format(sum(1 for k in value if k != 'data'), size),
        )

        results.extend(html_tree(value, scientific, lineage=[key] + lineage))

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
                print(identifier)
                continue

            html += """
            <a data-fancybox="gallery" data-caption="{name}" href="{fullsize}">
                <img src="/imgs/{thumbnail}" alt="">
            </a>
            """.format(
                name='{} - {}'.format(image.name, image.directory),
                fullsize=image.fullsize(),
                thumbnail=image.hash(),
            )

            seen.add(identifier)
        html += "</div>"

    html += """
    </body>
    </html>
    """

    if title == "Diving Gallery":
        title = "index"

    results.append((title, html))

    return results


def pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "gallery/{name}.html".format(name=title.replace(" ", "-"))

    with open(path, "w+") as f:
        print(html, file=f)


def write_all_html():
    ''' main '''
    pool = multiprocessing.Pool()

    print("loading data... ", end="", flush=True)
    tree = collection.go()
    scientific = taxonomy.mapping()
    print("done", tree_size(tree), "images loaded")

    print("walking tree... ", end="", flush=True)
    htmls = html_tree(tree, scientific)
    print("done", len(htmls), "pages prepared")

    print("writing html... ", end="", flush=True)
    pool.map(pool_writer, htmls)
    print("done")


# resources

html_scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery.min.js"></script>
    <script src="/jquery.fancybox.min.js"></script>
"""


if not sys.flags.interactive and __name__ == "__main__":
    if len(sys.argv) == 2:
        root = sys.argv[1]

    write_all_html()
