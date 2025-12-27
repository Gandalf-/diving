#!/usr/bin/python3

"""
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
"""

import multiprocessing
import statistics
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple, cast

import imprecise
from diving import detective, hypertext, information, locations, search, timeline
from diving.hypertext import Side, Where
from util import collection, resource, static, taxonomy, verify
from util.common import (
    Progress,
    Tree,
    extract_leaves,
    file_content_matches,
    is_date,
    pretty_date,
    sanitize_link,
    strip_date,
    titlecase,
    tree_size,
)
from util.image import Image
from util.metrics import metrics
from util.similarity import similarity

# Similar species configuration
SIMILAR_SPECIES_COUNT = 4
SIMILAR_SPECIES_THRESHOLD = 0.75  # Excludes weaker order-level matches

# Type alias for precomputed similar species
SimilarSpeciesMap = dict[str, List[Tuple[str, float]]]


@dataclass
class SimilarSpeciesContext:
    """Context for similar species rendering (Gallery/Taxonomy only)."""

    flat_tree: dict[str, List[Image]]
    similar_map: SimilarSpeciesMap
    scientific_for_links: dict[str, str]


def build_similar_species_map(
    all_names: set[str],
    taxonomy_tree: dict[str, str],
) -> SimilarSpeciesMap:
    """Precompute similar species for all names at once."""
    # Filter to names with taxonomy
    valid_names = {name for name in all_names if name in taxonomy_tree}

    def is_generic(name: str) -> bool:
        """Check if this is a generic sp. entry."""
        return taxonomy_tree[name].endswith(' sp.')

    result: SimilarSpeciesMap = {}
    for name in valid_names:
        if is_generic(name):
            continue

        name_taxonomy = taxonomy_tree[name]
        scores = []

        for other in valid_names:
            if other == name or is_generic(other):
                continue

            score = similarity(name_taxonomy, taxonomy_tree[other])
            if score >= SIMILAR_SPECIES_THRESHOLD:
                scores.append((other, score))

        if scores:
            # Sort by score DESC, then name ASC for deterministic tie-breaking
            scores.sort(key=lambda x: (-x[1], x[0]))
            result[name] = scores[:SIMILAR_SPECIES_COUNT]

    return result


def html_similar_species(
    similar: List[Tuple[str, float]],
    flat_tree: dict[str, List[Image]],
    where: Where,
    scientific: dict[str, str],
) -> str:
    """Generate HTML for similar species section."""
    if not similar:
        return ''

    html = '<div class="similar-species">'
    html += '<p class="similar-header"><b>Similar Species</b></p>'
    html += '<div class="grid similar-grid">'

    for other_name, _ in similar:
        # Find images for this species
        images = flat_tree.get(other_name)
        if not images:
            continue

        # Get newest image as representative
        images = sorted(images, key=lambda x: x.path(), reverse=True)
        example = next((img for img in images if img.is_image), None)
        if not example:
            continue

        # Build link and display name based on target (gallery vs taxonomy)
        if where == Where.Taxonomy:
            taxonomy_path = scientific.get(other_name, '')
            if not taxonomy_path:
                continue
            link = f'/taxonomy/{taxonomy_path.replace(" ", "-")}'
            parts = taxonomy_path.split()
            if parts[-1].islower():
                display_name = ' '.join(parts[-2:])  # "Oxycomanthus bennetti"
            else:
                display_name = f'{parts[-1]} sp.'  # "Comissa sp."
        else:
            link = f'/gallery/{sanitize_link(example.normalized())}'
            display_name = titlecase(other_name)

        html += f"""
        <div class="card">
          <a href="{link}">
            <div class="zoom-wrapper">
              <img class="zoom" height=150 width=200 alt="{other_name}" src="{example.thumbnail()}">
            </div>
            <h4 class="similar">{display_name}</h4>
          </a>
        </div>
        """

    html += '</div></div>'
    return html


def _prefer_single_subject(images: List[Image], pick_middle: bool = False) -> Image:
    """Select an image, preferring single-subject images."""
    single = [img for img in images if not img.has_multiple_subjects()]
    candidates = single if single else images
    if pick_middle:
        return candidates[len(candidates) // 2]
    return candidates[0]


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

    if where == Where.Sites:
        items = list(results)
        return _prefer_single_subject(items, pick_middle=True)

    results = sorted(results, key=lambda image: image.path(), reverse=True)
    assert results, (tree, lineage)
    return _prefer_single_subject(results, pick_middle=False)


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
        seen: set[str] = set()
        htmls = []
        for part in information.lineage_to_names(lineage):
            html, url = information.html(part)
            if url not in seen:
                seen.add(url)
                htmls.append(html)
        return '<br>'.join(htmls)

    if where == Where.Gallery and direct:
        return get_gallery_info(direct)

    return ''


def _key_to_subject(key: str, where: Where) -> str:
    if where == Where.Gallery:
        scientific = taxonomy.is_scientific_name(key)
        return f'<em>{scientific}</em>' if scientific else titlecase(key)

    if where == Where.Sites:
        subject = strip_date(key)
        return pretty_date(subject) if is_date(subject) else subject

    return taxonomy.simplify(key, shorten=True)


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


def _render_category_card(
    example: Image,
    subject: str,
    where: Where,
    lineage: List[str],
    side: Side,
    key: str,
    size: int,
    subcategories: int,
) -> str:
    """Render a single category card for the grid."""
    hint = f'{subcategories} · {size}' if subcategories else f'{size}'
    return """
        <div class="card">
        <a href="{link}">
            <div class="zoom-wrapper">
              <img class="zoom" height=225 width=300 alt="{alt}" src="{thumbnail}">
            </div>
            <h3 class="label-row">
              <span> </span>
              <span>{subject}</span>
              <span class="count">{hint}</span>
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
        hint=hint,
    )


def _get_similar_species_html(
    direct: List[Image],
    lineage: List[str],
    similar_ctx: Optional[SimilarSpeciesContext],
    where: Where,
) -> str:
    """Get the similar species HTML section if applicable."""
    if not (direct and lineage and similar_ctx):
        return ''

    name = direct[0].simplified()
    similar = similar_ctx.similar_map.get(name)
    if not similar:
        return ''

    return html_similar_species(
        similar, similar_ctx.flat_tree, where, similar_ctx.scientific_for_links
    )


def _page_footer(info: str, similar_html: str) -> str:
    """Generate the page footer HTML."""
    now = datetime.now()
    return f"""
      {info}
      {similar_html}
      </div>
      <footer>
        <p><a href="https://goto.anardil.net">goto.anardil.net</a></p>
        <p>austin@anardil.net {now.year}</p>
      </footer>
      {hypertext.scripts}
    </body>
    </html>
    """


def _process_category(
    key: str,
    value: collection.ImageTree,
    where: Where,
    lineage: List[str],
    side: Side,
    scientific: taxonomy.NameMapping,
    similar_ctx: Optional[SimilarSpeciesContext],
) -> Tuple[str, List[Tuple[str, str]]]:
    """Process a single category and return (html, child_results)."""
    new_lineage = [key] + lineage if side == Side.Left else lineage + [key]
    example = find_representative(value, where, new_lineage)
    assert example.is_image
    subject = _key_to_subject(key, where)

    size = tree_size(value)
    subcategories = sum(1 for k in value if k != 'data')

    card_html = _render_category_card(
        example, subject, where, lineage, side, key, size, subcategories
    )

    child_results = html_tree(value, where, scientific, new_lineage, similar_ctx)
    return card_html, child_results


def html_tree(
    tree: collection.ImageTree,
    where: Where,
    scientific: taxonomy.NameMapping,
    lineage: Optional[List[str]] = None,
    similar_ctx: Optional[SimilarSpeciesContext] = None,
) -> List[Tuple[str, str]]:
    """html version of display"""
    lineage = lineage or []
    assert similar_ctx is None or where in (Where.Gallery, Where.Taxonomy)
    side = Side.Left if where == Where.Gallery else Side.Right

    html, path = hypertext.title(lineage, where, scientific)

    results = []
    has_subcategories = any(key != 'data' for key in tree.keys())
    if has_subcategories:
        html += '<div class="grid">'

    flip = where == Where.Sites and any(is_date(v) for v in tree.keys())
    for key, value in sorted(tree.items(), reverse=flip):
        if key == 'data':
            continue
        value = cast(collection.ImageTree, value)
        card_html, child_results = _process_category(
            key, value, where, lineage, side, scientific, similar_ctx
        )
        html += card_html
        results.extend(child_results)

    if has_subcategories:
        html += '</div>'

    direct = cast(List[Image], tree.get('data', []))
    chronological = where != Where.Sites
    direct = sorted(direct, key=lambda x: x.path(), reverse=chronological)
    assert not (direct and has_subcategories)

    if direct:
        html += html_direct_examples(direct, where)

    info = get_info(where, lineage, direct)
    similar_html = _get_similar_species_html(direct, lineage, similar_ctx, where)
    html += _page_footer(info, similar_html)

    results.append((path, html))
    return results


def main() -> None:
    """main"""
    with Progress('loading images'):
        tree = collection.build_image_tree()
        scientific = taxonomy.mapping()
        taxia = taxonomy.gallery_tree(tree)

        # Precompute for similar species (gallery and taxonomy)
        flat_tree = collection.single_level(tree)
        all_species = set(flat_tree.keys())
        similar_map = build_similar_species_map(all_species, scientific)
        similar_ctx = SimilarSpeciesContext(
            flat_tree=flat_tree,
            similar_map=similar_map,
            scientific_for_links=scientific,
        )

    with Progress('building /gallery'):
        name_htmls = html_tree(tree, Where.Gallery, scientific, similar_ctx=similar_ctx)

    with Progress('building /sites'):
        sites = locations.sites()
        sites_htmls = html_tree(sites, Where.Sites, scientific)

    with Progress('building /taxonomy'):
        scientific_reversed = {v: k for k, v in scientific.items()}
        taxia_htmls = html_tree(taxia, Where.Taxonomy, scientific_reversed, similar_ctx=similar_ctx)

    with Progress('building /timeline'):
        times_htmls = timeline.timeline()

    with Progress('building /detective'):
        detective.writer()

    metrics.counter('images loaded', tree_size(tree))
    metrics.counter('pages in gallery', len(name_htmls))
    metrics.counter('pages in sites', len(sites_htmls))
    metrics.counter('pages in taxonomy', len(taxia_htmls))
    metrics.counter('pages in timeline', len(times_htmls))
    metrics.counter('imprecise labels', imprecise.total_imprecise())

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
