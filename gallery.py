#!/usr/bin/python3

'''
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
'''

import os
import sys
import multiprocessing
import textwrap
from datetime import datetime
from typing import Tuple, Optional, List, cast

import detective
import hypertext
import information
import locations
import search
import timeline

from util import collection
from util import static
from util import taxonomy
from util import verify
from util.metrics import metrics
from util.image import Image
from util.common import (
    tree_size,
    extract_leaves,
    is_date,
    strip_date,
    pretty_date,
    prefix_tuples,
    titlecase,
    file_content_matches,
    sanitize_link,
    Tree,
)

from hypertext import Where, Side

# pylint: disable=too-many-locals
# pylint: disable=line-too-long


def find_representative(tree: Tree, lineage: Optional[List[str]] = None) -> Image:
    """Find one image to represent this tree."""
    lineage = lineage or []
    pinned = static.pinned.get(' '.join(lineage))

    if pinned:
        found = _find_by_path(tree, pinned)
        if found:
            return found

    results = extract_leaves(tree)
    results = sorted(results, key=lambda image: image.path(), reverse=True)

    assert results, (tree, lineage)
    return results[0]


def get_info(where: Where, lineage: List[str]) -> str:
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


def _key_to_subject(key: str, where: Where) -> str:
    '''helper!'''
    if where == Where.Gallery:
        subject = taxonomy.is_scientific_name(key)
        if not subject:
            subject = titlecase(key)
        else:
            subject = f'<em>{subject}</em>'

    elif where == Where.Sites:
        subject = strip_date(key)
        if is_date(subject):
            subject = pretty_date(subject)

    else:
        subject = taxonomy.simplify(key, shorten=True)

    return subject


def html_direct_examples(direct: List[Image], where: Where) -> str:
    '''
    Generate the HTML for the direct examples of a tree.
    '''
    seen = set()
    html = '<div class="grid">'

    for i, image in enumerate(direct):
        identifier = tuple([image.name, image.path()])
        if identifier in seen:
            continue

        name_html = hypertext.image_to_name_html(image, where)
        site_html = hypertext.image_to_site_html(image, where)

        html += """
        <div class="card" onclick="flip(this);">
            <div class="card_face card_face-front">
            <img height=225 width=300 {lazy} alt="{name}" src="{thumbnail}">
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
            lazy='loading="lazy"' if i > 16 else '',
            site_html=site_html,
            location=image.location(),
            fullsize=image.fullsize(),
            thumbnail=image.thumbnail(),
        )

        seen.add(identifier)
    html += "</div>"

    return html


def html_tree(
    tree: collection.ImageTree,
    where: Where,
    scientific: taxonomy.NameMapping,
    lineage: Optional[List[str]] = None,
) -> List[Tuple[str, str]]:
    """html version of display"""
    lineage = lineage or []
    side = Side.Left if where == Where.Gallery else Side.Right

    # title
    html, title = hypertext.title(lineage, where, scientific)

    # body
    results = []
    has_subcategories = any(key != "data" for key in tree.keys())
    if has_subcategories:
        html += '<div class="grid">'

    # categories
    flip = where == Where.Sites and any(is_date(v) for v in tree.keys())
    for key, value in sorted(tree.items(), reverse=flip):
        if key == "data":
            continue

        new_lineage = [key] + lineage if side == Side.Left else lineage + [key]
        size = tree_size(value)
        example = find_representative(value, new_lineage)
        subject = _key_to_subject(key, where)

        html += """
        <div class="image">
        <a href="{link}">
            <img height=225 width=300 alt="{alt}" src="{thumbnail}">
            <h3 class="tight">
              <span class="sneaky">{size}</span>
              {subject}
              <span class="count">{size}</span>
            </h3>
        </a>
        </div>
        """.format(
            alt=example.simplified(),
            subject=subject,
            link="/{where}/{path}".format(
                where=where.name.lower(),
                path=hypertext.lineage_to_link(lineage, side, key),
            ),
            thumbnail=example.thumbnail(),
            size='{}:{}'.format(sum(1 for k in value if k != 'data') or '', size),
        )

        value = cast(collection.ImageTree, value)
        results.extend(html_tree(value, where, scientific, lineage=new_lineage))

    if has_subcategories:
        html += "</div>"

    # direct examples
    direct = cast(List[Image], tree.get("data", []))
    chronological = where != Where.Sites
    direct = sorted(direct, key=lambda x: x.path(), reverse=chronological)
    assert not (direct and has_subcategories)

    if direct:
        html += html_direct_examples(direct, where)

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

    path = sanitize_link(title) + '.html'
    results.append((path, html))
    return results


def write_all_html() -> None:
    '''main'''

    print("loading images...              ", end="", flush=True)
    tree = collection.build_image_tree()
    scientific = taxonomy.mapping()
    taxia = taxonomy.gallery_tree(tree)
    print("done", tree_size(tree), "images loaded")

    print("building /gallery...           ", end="", flush=True)
    name_htmls = html_tree(tree, Where.Gallery, scientific)
    print("done", len(name_htmls), "pages prepared")

    print("building /sites...             ", end="", flush=True)
    sites = locations.sites()
    sites_htmls = html_tree(sites, Where.Sites, scientific)
    print("done", len(sites_htmls), "pages prepared")

    print("building /taxonomy...          ", end="", flush=True)
    scientific = {v: k for k, v in scientific.items()}
    taxia_htmls = html_tree(taxia, Where.Taxonomy, scientific)
    print("done", len(taxia_htmls), "pages prepared")

    print("building /timeline...          ", end="", flush=True)
    times_htmls = timeline.timeline()
    print("done", len(times_htmls), "pages prepared")

    print("building /detective...         ", end="", flush=True)
    detective.writer()
    print("done")

    print("writing html...                ", end="", flush=True)

    for vr in [static.search_js, static.stylesheet]:
        vr.cleanup()
        vr.write()

    with multiprocessing.Pool() as pool:
        pool.map(_pool_writer, prefix_tuples('gallery', name_htmls))
        pool.map(_pool_writer, prefix_tuples('sites', sites_htmls))
        pool.map(_pool_writer, prefix_tuples('taxonomy', taxia_htmls))
        pool.map(_pool_writer, prefix_tuples('timeline', times_htmls))
    print("done")


def _pool_writer(args: Tuple[str, str, str]) -> None:
    '''callback for HTML writer pool'''
    where, title, html = args
    html = textwrap.dedent(html)
    path = f"{where}/{title}"

    if file_content_matches(path, html):
        return

    with open(path, "w+") as f:
        print(html, file=f, end='')


def _find_by_path(tree: Tree, needle: str) -> Optional[Image]:
    """search the tree for an image with this path"""
    for leaf in extract_leaves(tree):
        if needle in leaf.path():
            return leaf
    return None


if not sys.flags.interactive and __name__ == "__main__":
    import util.common

    if len(sys.argv) > 1:
        util.common.image_root = sys.argv[1]

    write_all_html()
    search.write_search_data()

    if not os.environ.get('DIVING_FAST'):
        print("verifying html...              ", end="", flush=True)
        if os.environ.get('DIVING_VERIFY'):
            verify.required_checks()
        else:
            verify.advisory_checks()
    print("done")

    metrics.summary()
