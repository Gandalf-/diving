#!/usr/bin/python3

'''
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
'''

import re
import os
import sys
import multiprocessing
from datetime import datetime

import hypertext
import information
import locations
import taxonomy
import timeline
import collection
import static

from detective import javascript as game
from hypertext import Where, Side
from image import Image
from util.common import tree_size, is_date, strip_date

# pylint: disable=too-many-locals
# pylint: disable=line-too-long


def find_representative(tree, lineage=None):
    """grab one image to represent this tree"""
    if not lineage:
        lineage = []

    # forwards for gallery
    category = ' '.join(lineage)
    if category in static.pinned:
        found = _find_by_path(tree, static.pinned[category])
        if found:
            return found

    # backwards for taxonomy
    category = ' '.join(lineage[::-1])
    if category in static.pinned:
        found = _find_by_path(tree, static.pinned[category])
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


def get_info(where, lineage):
    """wikipedia information if available"""
    if where != Where.Taxonomy:
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


def _key_to_subject(key, where):
    ''' helper!
    '''
    if where == Where.Gallery:
        subject = taxonomy.is_scientific_name(key)
        if not subject:
            subject = key.title()
        else:
            subject = f'<em>{subject}</em>'

    elif where == Where.Sites:
        subject = strip_date(key).title().replace("'S", "'s")
    else:
        subject = taxonomy.simplify(key)

    return subject


def html_tree(tree, where, scientific, lineage=None):
    """html version of display"""
    if not lineage:
        lineage = []

    side = Side.Left if where == Where.Gallery else Side.Right

    html, title = hypertext.title(lineage, where, scientific)
    results = []

    has_subcategories = [1 for key in tree.keys() if key != "data"] != []
    if has_subcategories:
        html += '<div class="grid">'

    # categories
    flip = where == Where.Sites and any(is_date(v) for v in tree.keys())
    for key, value in sorted(tree.items(), reverse=flip):
        if key == "data":
            continue

        new_lineage = [key] + lineage if side == Side.Left else lineage + [key]
        size = tree_size(value)
        example = find_representative(value, [key] + lineage)
        subject = _key_to_subject(key, where)

        html += """
        <div class="image">
        <a href="{link}">
            <img width=300 loading="lazy" alt="{alt}" src="/imgs/{thumbnail}">
            <h3>
              <span class="sneaky">{size}</span>
              {subject}
              <span class="count">{size}</span>
            </h3>
        </a>
        </div>
        """.format(
            alt=example.simplified(),
            subject=subject,
            link="/{where}/{path}.html".format(
                where=where.name.lower(),
                path=hypertext.lineage_to_link(lineage, side, key),
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

            name_html = hypertext.image_to_name_html(image, where)
            site_html = hypertext.image_to_site_html(image, where)

            html += """
            <div class="card" onclick="flip(this);">
              <div class="card_face card_face-front">
                <img width=300 loading="lazy" src="/imgs/{thumbnail}">
              </div>
              <div class="card_face card_face-back">
                {name_html}
                {site_html}
                <a class="top elem timeline" data-fancybox="gallery" data-caption="{name} - {location}" href="{fullsize}">
                Fullsize Image
                </a>
                <p class="top elem">Close</p>
              </div>
            </div>
            """.format(
                name=image.name,
                name_html=name_html,
                site_html=site_html,
                location=image.location(),
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
      {hypertext.scripts}
    </body>
    </html>
    """

    if title in ('Gallery', 'Taxonomy', 'Sites'):
        title = 'index'

    results.append((title, html))
    return results


def names_pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "gallery/{name}.html".format(name=title.replace(" ", "-"))
    with open(path, "w+") as f:
        print(html, file=f)


def sites_pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "sites/{name}.html".format(
        name=title.replace(" ", "-").replace("'", '')
    )
    with open(path, "w+") as f:
        print(html, file=f)


def taxia_pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "taxonomy/{name}.html".format(name=title.replace(" ", "-"))
    with open(path, "w+") as f:
        print(html, file=f)


def times_pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = f"timeline/{title}"
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
    name_htmls = html_tree(tree, Where.Gallery, scientific)
    print("done", len(name_htmls), "pages prepared")

    print("walking sites tree... ", end="", flush=True)
    sites = locations.sites()
    sites_htmls = html_tree(sites, Where.Sites, scientific)
    print("done", len(sites_htmls), "pages prepared")

    print("walking taxia tree... ", end="", flush=True)
    scientific = {v.replace(' sp', ''): k for k, v in scientific.items()}
    taxia_htmls = html_tree(taxia, Where.Taxonomy, scientific)
    print("done", len(taxia_htmls), "pages prepared")

    print("walking timeline...   ", end="", flush=True)
    times_htmls = timeline.timeline()
    print("done", len(times_htmls), "pages prepared")

    print("writing html... ", end="", flush=True)
    pool.map(names_pool_writer, name_htmls)
    pool.map(sites_pool_writer, sites_htmls)
    pool.map(taxia_pool_writer, taxia_htmls)
    pool.map(times_pool_writer, times_htmls)
    print("done")

    print("writing game... ", end="", flush=True)
    game(False)
    print("done")


def _find_by_path(tree, needle):
    """search the tree for an image with this path"""
    if not isinstance(tree, dict):
        for image in tree:
            if needle in image.path():
                return image
    else:
        for child in tree.values():
            found = _find_by_path(child, needle)
            if found:
                return found

    return None


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

    for directory in ('taxonomy', 'gallery', 'sites'):
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


if not sys.flags.interactive and __name__ == "__main__":
    if len(sys.argv) == 2:
        root = sys.argv[1]

    write_all_html()
    link_check()
