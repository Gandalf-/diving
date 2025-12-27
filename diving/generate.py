"""Site generation orchestration.

Coordinates building all sections (gallery, sites, taxonomy, timeline, detective)
and writing HTML output.
"""

import multiprocessing
import textwrap
from typing import List, Tuple

from diving import detective, imprecise, locations, search, timeline
from diving.gallery import SimilarSpeciesContext, build_similar_species_map, html_tree
from diving.hypertext import Where
from diving.util import collection, resource, taxonomy
from diving.util.common import Progress, file_content_matches, tree_size
from diving.util.metrics import metrics


def main() -> None:
    """Generate the complete diving website."""
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
    """Callback for HTML writer pool."""
    path, html = args
    html = textwrap.dedent(html)

    if file_content_matches(path, html):
        return

    with open(path, 'w+') as f:
        print(html, file=f, end='')


def _get_paths(htmls: List[Tuple[str, str]]) -> List[str]:
    """Extract paths from html tuples."""
    return [p for p, _ in htmls]
