#!/usr/bin/python3

'''
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
'''

import sys
import multiprocessing

import taxonomy
import collection

from image import uncategorize, Image
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

    def get_path(image):
        assert isinstance(image, Image), image
        return image.path()

    results = sorted(results, key=get_path, reverse=True)
    return results[0]


def lineage_to_link(lineage, side, key=None):
    ''' get a link to this page
    '''
    if not lineage:
        name = key
    else:
        name = ' '.join(lineage)

        if key and side == 'left':
            name = key + ' ' + name

        if key and side == 'right':
            name = name + ' ' + key

    return name.replace(' ', '-')


def html_title(lineage, side, where, scientific=None):
    ''' html head and title section
    '''
    title = " ".join(lineage) or "Diving Gallery"
    display = uncategorize(title).title()

    # always have a link to the top level of the gallery
    top_level = """
        <a href="/{where}/index.html">
            <h1 class="top switch">Diving {title}</h1>
        </a>
    """.format(
        where=where, title=where.title()
    )

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

    if side == 'right':
        html += top_level

    # create the buttons for each part of our name lineage
    for i, name in enumerate(lineage):

        if side == 'left':
            partial = lineage[i:]
        else:
            partial = lineage[: i + 1]

        link = "/{where}/{path}.html".format(
            where=where, path=lineage_to_link(partial, side)
        )
        last = i == len(lineage) - 1

        html += """
        <a href="{link}">
            <h1 class="{classes}">{title}</h1>
        </a>
        """.format(
            title=name.title(),
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

    if side == 'left':
        html += top_level

    # check for scientific name for gallery
    if where == 'gallery':
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
        """

    html += "</div>"

    return html, title


def html_tree(tree, where, scientific, lineage=None):
    """ html version of display
    """
    if not lineage:
        lineage = []

    side = 'left' if where == 'gallery' else 'right'

    html, title = html_title(lineage, side, where, scientific)
    results = []

    has_subcategories = [1 for key in tree.keys() if key != "data"] != []
    if has_subcategories:
        html += '<div class="grid">'

    # categories
    for key, value in sorted(tree.items()):
        if key == "data":
            continue

        size = tree_size(value)
        example = find_representative(value, [key] + lineage)

        if side == 'right':
            print(lineage)

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
            link="/{where}/{path}.html".format(
                where=where, path=lineage_to_link(lineage, side, key),
            ),
            thumbnail=example.hash(),
            size='{}:{}'.format(sum(1 for k in value if k != 'data'), size),
        )

        results.extend(
            html_tree(
                value,
                where,
                scientific,
                lineage=[key] + lineage if side == 'left' else lineage + [key],
            )
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
    taxia_htmls = html_tree(taxia, "taxonomy", scientific)
    print("done", len(taxia_htmls), "pages prepared")

    print("writing html... ", end="", flush=True)
    pool.map(names_pool_writer, name_htmls)
    pool.map(taxia_pool_writer, taxia_htmls)
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
