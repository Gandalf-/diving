#!/usr/bin/python3

"""
taxonomy related things

- parsing and dealing with taxonomy.yml
- updating taxonomy.txt so it's clear what's missing
- searching the classification tree for fuzzy matches to common names
- simplification of full classification into reasonable abbreviations
"""

import enum
import os
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union

import yaml

from util import static
from util.collection import ImageTree, all_names, build_image_tree, single_level
from util.common import extract_branches, extract_leaves, hmap
from util.image import Image, uncategorize, unqualify, unsplit
from util.metrics import metrics

yaml_path = os.path.join(static.source_root, 'data/taxonomy.yml')

TaxiaTree = dict[str, Union[str, 'TaxiaTree']]
NameMapping = dict[str, str]


def gallery_scientific(lineage: List[str], scientific: NameMapping, debug: bool = False) -> str:
    """attempt to find a scientific name for this page"""

    def lookup(names: List[str], *fns: Callable) -> Optional[str]:
        base = ' '.join(names).lower()
        candidate = hmap(base, *fns)
        return scientific.get(candidate)

    attempts = [
        (lineage, [uncategorize, unqualify]),
        (lineage, [uncategorize, unqualify, unsplit]),
        (lineage[1:], [uncategorize, unqualify, unsplit]),
        (lineage[2:], [uncategorize, unqualify, unsplit]),
    ]

    for ln, fns in attempts:
        name = lookup(ln, *fns)
        if name:
            break

    if not name and not no_taxonomy(lineage):
        metrics.record('no scientific name', ' '.join(lineage))

    return name or ''


def no_taxonomy(lineage: List[str]) -> bool:
    """is this lineage not in the taxonomy?"""
    name = ' '.join(lineage)
    if unqualify(uncategorize(name)) in static.no_taxonomy_exact:
        metrics.counter('lineages known to not have taxonomy')
        return True

    if any(i in name for i in static.no_taxonomy_any):
        metrics.counter('lineages known to not have taxonomy')
        return True

    return False


def simplify(name: str, shorten: bool = False) -> str:
    """Try to simplify the lineage by abbreviating repeated prefixes.
    Diadematoida Diadematidae Diadema antillarum -> to D. D. Diadema antillarum
    """
    if ' ' not in name:
        return name

    parts = name.split(' ')
    lefts, rights = parts[:-1], parts[1:]
    out = []

    for a, b in zip(lefts, rights):
        if similar(a, b):
            out.append(a[0].upper() + '.')
        else:
            out.append(a)

    out.append(parts[-1])

    # shorten very long names
    result = ' '.join(out)
    shortened = False

    while shorten and len(result) > 30:
        shortened = True
        out = [out[0]] + out[2:]
        result = ' '.join(out)

    if shortened:
        result = ' '.join([out[0], '...'] + out[1:])

    return result


def similar(a: str, b: str) -> bool:
    """determine if two words are similar, usually a super family and family,
    or something to that effect
    """
    length = (len(a) + len(b)) // 2
    pivot = length // 2

    return a[:pivot] == b[:pivot]


@lru_cache(None)
def load_tree() -> TaxiaTree:
    """yaml load"""
    with open(yaml_path, encoding='utf8') as fd:
        return yaml.safe_load(fd)


def load_known(exact_only: bool = False) -> Iterable[str]:
    """load taxonomy.yml"""

    tree = load_tree()
    if exact_only:
        tree = _filter_exact(tree)

    yield from extract_leaves(tree)


def all_latin_words() -> Set[str]:
    def producer() -> Iterable[str]:
        for branch in extract_branches(load_tree()):
            yield from branch.split(' ')

    result = set(word.lower() for word in producer())
    result.remove('sp.')
    return result


MappingType = enum.Enum('MappingType', 'Gallery Taxonomy')


@lru_cache(None)
def mapping(where: MappingType = MappingType.Gallery) -> NameMapping:
    """
    gallery:  mapping of common names to scientific names
    taxonomy: mapping of scientific names to common names
    """
    tree = _invert_known(load_tree())

    if where == MappingType.Gallery:
        return tree

    return {v: k for k, v in tree.items()}


def gallery_tree(tree: Optional[ImageTree] = None) -> ImageTree:
    """produce a tree for gallery.py to use
    the provided tree must be from collection.build_image_tree()
    """
    tree = tree or build_image_tree()

    images = single_level(tree)
    taxia = compress_tree(load_tree())
    itree = _taxia_filler(taxia, images)

    return itree


def binomial_names(tree: Optional[Any] = None, parent: Optional[str] = None) -> Iterable[str]:
    """scientific binomial names"""
    tree = tree or load_tree()

    if not isinstance(tree, dict):
        return

    for key, value in tree.items():
        if key.islower() and key != 'sp.':
            assert parent, key
            yield f'{parent} {key}'
        else:
            yield from binomial_names(value, parent=key)


def looks_like_scientific_name(name: str) -> bool:
    """Genus species Other Other"""
    parts = name.split(' ')
    if len(parts) < 2:
        return False

    genus = parts[0]
    species = parts[1]

    return genus.istitle() and species.islower()


def is_scientific_name(name: str) -> Optional[str]:
    """cached lookup"""
    return names_cache().get(name.lower())


# PRIVATE


@lru_cache(None)
def names_cache() -> NameMapping:
    """cached lookup"""
    cache = {}
    for bname in binomial_names():
        cache[bname.lower()] = bname

        genus, _ = bname.split()
        cache[genus.lower()] = genus

    return cache


def _to_classification(name: str, mappings: NameMapping) -> str:
    """find a suitable classification for this common name"""
    return gallery_scientific(name.split(' '), mappings)


def _filter_exact(tree: TaxiaTree) -> TaxiaTree:
    """remove all sp. entries"""
    assert isinstance(tree, dict), tree

    out: TaxiaTree = {}
    for key, value in tree.items():
        if key == 'sp.':
            continue

        if isinstance(value, dict):
            out[key] = _filter_exact(value)
        else:
            out[key] = value

    return out


def compress_tree(tree: TaxiaTree) -> TaxiaTree:
    """
    Collapse subtrees with only one child into their parent and update the parent's
    key for the current subtree to be "key + child key".
    """
    out = {}

    for key, value in tree.items():
        if isinstance(value, dict):
            sub_tree = compress_tree(value)

            if len(sub_tree) == 1:
                child_key, child_value = next(iter(sub_tree.items()))
                new_key = key + ' ' + child_key
                out[new_key] = child_value
            else:
                out[key] = sub_tree
        else:
            out[key] = value

    return out


def _taxia_filler(tree: TaxiaTree, images: Dict[str, List[Image]]) -> ImageTree:
    """fill in the images"""
    assert isinstance(tree, dict), tree
    out: ImageTree = {}

    for key, value in list(tree.items()):
        if isinstance(value, str):
            if not value.islower():
                assert False, f'taxonomy.yml keys must be lowercase: {key}'

            if value in images:
                out[key] = {'data': images[value]}
        else:
            out[key] = _taxia_filler(value, images)

    return out


def _invert_known(tree: TaxiaTree) -> NameMapping:
    """leaves become roots"""

    result: Dict[str, str] = {}

    def inner(
        tree: Union[str, 'TaxiaTree'],
        out: Dict[str, str],
        lineage: Optional[List[str]] = None,
    ) -> None:
        if not lineage:
            lineage = []

        if isinstance(tree, str):
            for part in tree.split(', '):
                out[part] = ' '.join(lineage)
        else:
            for key, value in tree.items():
                inner(value, out, lineage + [key])

    inner(tree, result)
    return result


# INFORMATIONAL


def _ordered_simple_names(tree: ImageTree) -> Iterable[str]:
    """taxonomy names"""
    assert isinstance(tree, dict), tree

    for value in tree.values():
        if isinstance(value, dict):
            yield from _ordered_simple_names(value)

        elif isinstance(value, list):
            yield value[0].simplified()

        else:
            assert False, value


def _find_imprecise() -> Iterable[str]:
    """find names with classifications that could be more specific"""
    names = all_names()
    m = mapping()

    for name in names:
        c = _to_classification(name, m)
        if ' sp.' in c:
            yield name
