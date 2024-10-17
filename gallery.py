#!/usr/bin/python3

"""
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
"""

import multiprocessing
import statistics
import sys
import textwrap
from datetime import datetime
from typing import List, Optional, Tuple, cast

import detective
import hypertext
import information
import locations
import search
import timeline
from hypertext import Side, Where
from util import collection, resource, static, taxonomy, verify
from util.common import (
    Progress,
    Tree,
    extract_leaves,
    file_content_matches,
    is_date,
    pretty_date,
    strip_date,
    titlecase,
    tree_size,
)
from util.image import Image
from util.metrics import metrics


def find_representative(tree: Tree, where: Where, lineage: Optional[List[str]] = None) -> Image:
    """Find one image to represent this tree."""
    lineage = lineage or []
    pinned = static.pinned.get(' '.join(lineage))

    if pinned:
        found = _find_by_path(tree, pinned)
        if found:
            return found

    results = (leaf for leaf in extract_leaves(tree) if leaf.is_image)
    assert results, (tree, lineage)

    if where == where.Sites:
        items = list(results)
        return items[len(items) // 2]

    results = sorted(results, key=lambda image: image.path(), reverse=True)
    assert results, (tree, lineage)
    return results[0]


def get_gallery_info(direct: List[Image]) -> str:
    parts = []
    measurements = [image.approximate_depth() for image in direct]
    depths = [m for m in measurements if m]

    if not depths or (len(depths) / len(measurements) < 0.5 and len(depths) < 5):
        metrics.counter('lineages without depth distribution')
    else:
        # questionable math going on here
        low = int(statistics.mean(low for low, _ in depths))
        high = max(h for _, h in depths)
        metrics.counter('lineages with depth distribution')
        parts.append(f"{low}' ~ {high}'")

    regions = sorted({locations.get_region(image.site()) for image in direct})
    parts.append(', '.join(regions))

    distribution = ' '.join(parts)
    return f"""
    <div class="info">
    <p><b>Distribution:</b> {distribution}</p>
    </div>"""


def get_info(where: Where, lineage: List[str], direct: List[Image]) -> str:
    """wikipedia information if available"""
    if where == Where.Taxonomy:
        htmls = []
        seen = set()

        for part in information.lineage_to_names(lineage):
            html, url = information.html(part)
            if url in seen:
                continue
            seen.add(url)
            htmls.append(html)
        return '<br>'.join(htmls)

    elif where == Where.Gallery and direct:
        return get_gallery_info(direct)

    else:
        return ''


def _key_to_subject(key: str, where: Where) -> str:
    """helper!"""
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
    """
    Generate the HTML for the direct examples of a tree.
    """
    seen = set()
    html = '<div class="grid">'

    for i, image in enumerate(direct):
        identifier = image.identifier()
        if identifier in seen:
            # This prevents 'b fish and b fish eggs' showing up twice on taxonomy pages
            continue
        html += hypertext.html_direct_image(image, where, i > 16)
        seen.add(identifier)

    html += '</div>'

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
    html, path = hypertext.title(lineage, where, scientific)

    # body
    results = []
    has_subcategories = any(key != 'data' for key in tree.keys())
    if has_subcategories:
        html += '<div class="grid">'

    # categories
    flip = where == Where.Sites and any(is_date(v) for v in tree.keys())
    for key, value in sorted(tree.items(), reverse=flip):
        if key == 'data':
            continue

        new_lineage = [key] + lineage if side == Side.Left else lineage + [key]
        size = tree_size(value)
        example = find_representative(value, where, new_lineage)
        assert example.is_image
        subject = _key_to_subject(key, where)

        html += """
        <div class="image">
        <a href="{link}">
            <div class="zoom-wrapper">
              <img class="zoom" height=225 width=300 alt="{alt}" src="{thumbnail}">
            </div>
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
            link='/{where}/{path}'.format(
                where=where.name.lower(),
                path=hypertext.lineage_to_link(lineage, side, key),
            ),
            thumbnail=example.thumbnail(),
            size='{}:{}'.format(sum(1 for k in value if k != 'data') or '', size),
        )

        value = cast(collection.ImageTree, value)
        results.extend(html_tree(value, where, scientific, lineage=new_lineage))

    if has_subcategories:
        html += '</div>'

    # direct examples
    direct = cast(List[Image], tree.get('data', []))
    chronological = where != Where.Sites
    direct = sorted(direct, key=lambda x: x.path(), reverse=chronological)
    assert not (direct and has_subcategories)

    if direct:
        html += html_direct_examples(direct, where)

    # additional info, like wikipedia and depth distribution
    info = get_info(where, lineage, direct)
    now = datetime.now()

    html += f"""
      {info}
      </div>
      <footer>
        <p><a href="https://goto.anardil.net">goto.anardil.net</a></p>
        <p>austin@anardil.net {now.year}</p>
      </footer>
      {hypertext.scripts}
    </body>
    </html>
    """

    results.append((path, html))
    return results


def main() -> None:
    """main"""
    with Progress('loading images'):
        tree = collection.build_image_tree()
        scientific = taxonomy.mapping()
        taxia = taxonomy.gallery_tree(tree)

    with Progress('building /gallery'):
        name_htmls = html_tree(tree, Where.Gallery, scientific)

    with Progress('building /sites'):
        sites = locations.sites()
        sites_htmls = html_tree(sites, Where.Sites, scientific)

    with Progress('building /taxonomy'):
        scientific = {v: k for k, v in scientific.items()}
        taxia_htmls = html_tree(taxia, Where.Taxonomy, scientific)

    with Progress('building /timeline'):
        times_htmls = timeline.timeline()

    with Progress('building /detective'):
        detective.writer()

    metrics.counter('images loaded', tree_size(tree))
    metrics.counter('pages in gallery', len(name_htmls))
    metrics.counter('pages in sites', len(sites_htmls))
    metrics.counter('pages in taxonomy', len(taxia_htmls))
    metrics.counter('pages in timeline', len(times_htmls))

    for vr in resource.registry:
        vr.cleanup()
        vr.write()

    with Progress('writing html'), multiprocessing.Pool() as pool:
        pool.map(_pool_writer, name_htmls)
        pool.map(_pool_writer, sites_htmls)
        pool.map(_pool_writer, taxia_htmls)
        pool.map(_pool_writer, times_htmls)

    search.write_search_data(
        _get_paths(name_htmls), _get_paths(sites_htmls), _get_paths(taxia_htmls)
    )


def _pool_writer(args: Tuple[str, str]) -> None:
    """callback for HTML writer pool"""
    path, html = args
    # TODO make this ASCII once I have the escape codes for the emojis
    html = textwrap.dedent(html)

    if file_content_matches(path, html):
        return

    with open(path, 'w+') as f:
        print(html, file=f, end='')


def _find_by_path(tree: Tree, needle: str) -> Optional[Image]:
    """search the tree for an image with this path"""
    for leaf in extract_leaves(tree):
        if needle in leaf.path():
            return leaf
    return None


def _get_paths(htmls: List[Tuple[str, str]]) -> List[str]:
    """helper"""
    return [p for p, _ in htmls]


if not sys.flags.interactive and __name__ == '__main__':
    import util.common

    if len(sys.argv) > 1:
        util.static.image_root = sys.argv[1]

    verify.verify_before()
    main()
    verify.verify_after()

    metrics.summary('gallery')
