#!/usr/bin/python3

'''
taxonomy related things

- parsing and dealing with taxonomy.yml
- updating taxonomy.txt so it's clear what's missing
- searching the classification tree for fuzzy matches to common names
- simplification of full classification into reasonable abbreviations
'''

import enum
import sys
import pathlib
from typing import Iterator

import yaml

from util.collection import build_image_tree, single_level, all_names
from util.common import extract_leaves, hmap
from util.image import uncategorize, unqualify, unsplit

root = str(pathlib.Path(__file__).parent.parent.absolute()) + '/'


def gallery_scientific(lineage, scientific, debug=False):
    '''attempt to find a scientific name for this page'''

    def lookup(names, *fns):
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

    if not name and debug:
        for skip in ('various', 'egg', 'unknown', 'wreck'):
            if skip in lineage:
                break
        else:
            print('no taxonomy', ' '.join(lineage))

    return name or ""


def simplify(name: str) -> str:
    '''try to use similar() to simplify the lineage by looking for repeated
    prefixes and abbreviating them

    Diadematoida Diadematidae Diadema antillarum
        to
    D. D. Diadema antillarum
    '''
    if ' ' not in name:
        return name

    parts = name.split(' ')
    lefts = parts[:-1]
    rights = parts[1:]

    out = []
    for a, b in zip(lefts, rights):
        if similar(a, b):
            out.append(a[0].upper() + '.')
        else:
            out.append(a)

    out.append(parts[-1])
    return ' '.join(out)


def similar(a, b):
    '''determine if two words are similar, usually a super family and family,
    or something to that effect
    '''
    length = sum([len(a), len(b)]) // 2
    pivot = int(length * 0.5)

    return a[:pivot] == b[:pivot]


def load_tree():
    '''yaml load'''
    with open(root + 'data/taxonomy.yml', encoding='utf8') as fd:
        return yaml.safe_load(fd)


def load_known(exact_only=False):
    '''load taxonomy.yml'''

    tree = load_tree()
    if exact_only:
        tree = _filter_exact(tree)

    for leaf in extract_leaves(tree):
        yield from leaf.split(', ')


MappingType = enum.Enum('MappingType', 'Gallery Taxonomy')


def mapping(where=MappingType.Gallery):
    '''simplified to scientific'''
    tree = _invert_known(load_tree())

    if where == MappingType.Gallery:
        return tree

    return {v: k for k, v in tree.items()}


def gallery_tree(tree=None):
    '''produce a tree for gallery.py to use
    the provided tree must be from collection.build_image_tree()
    '''
    if not tree:
        tree = build_image_tree()

    images = single_level(tree)
    taxia = _full_compress(load_tree())

    _taxia_filler(taxia, images)

    return taxia


def binomial_names(tree=None, parent=None) -> Iterator[str]:
    '''scientific binomial names'''
    if not tree:
        tree = load_tree()

    if not isinstance(tree, dict):
        return

    for key, value in tree.items():
        if key.islower() and key != 'sp.':
            assert parent, key
            yield f'{parent} {key}'
        else:
            yield from binomial_names(value, parent=key)


def looks_like_scientific_name(name: str) -> bool:
    '''Genus species Other Other'''
    parts = name.split(' ')
    if len(parts) < 2:
        return False

    genus = parts[0]
    species = parts[1]

    return genus.istitle() and species.islower()


def is_scientific_name(name):
    '''cached lookup'''
    if not _NAMES_CACHE:
        for bname in binomial_names():
            _NAMES_CACHE[bname.lower()] = bname

            genus, _ = bname.split()
            _NAMES_CACHE[genus.lower()] = genus

    return _NAMES_CACHE.get(name.lower())


# PRIVATE

_NAMES_CACHE = {}


def _to_classification(name, mappings):
    '''find a suitable classification for this common name'''
    return gallery_scientific(name.split(' '), mappings)


def _filter_exact(tree):
    '''remove all sp. entries'''
    assert isinstance(tree, dict), tree

    out = {}
    for key, value in tree.items():
        if key == 'sp.':
            continue

        if isinstance(value, dict):
            out[key] = _filter_exact(value)
        else:
            out[key] = value

    return out


def _compress(tree):
    '''squash levels'''
    if isinstance(tree, str):
        # hit a leaf
        return tree

    out = {}

    for key, value in list(tree.items()):

        if isinstance(value, str):
            out[key] = value
            continue

        if len(value.keys()) == 1:
            child = list(value.keys())[0]

            # squash
            new_key = key + ' ' + child
            out[new_key] = _compress(value[child])
        else:
            out[key] = _compress(value)

    return out


def _full_compress(tree):
    '''keep compressing until nothing changes'''
    old = tree

    while True:
        new = _compress(old)
        if new == old:
            break
        old = new

    return new


def _taxia_filler(tree, images):
    '''fill in the images'''
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if isinstance(value, str):
            if not value.islower():
                assert False, f'taxonomy.yml keys must be lowercase: {key}'

            if value in images:
                tree[key] = {'data': images[value]}
            else:
                tree.pop(key)
        else:
            tree[key] = _taxia_filler(value, images)

    return tree


def _invert_known(tree):
    '''leaves become roots'''

    result = {}

    def inner(tree, out, lineage=None):
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


def _ordered_simple_names(tree):
    '''taxonomy names'''
    assert isinstance(tree, dict), tree

    for value in tree.values():
        if isinstance(value, dict):
            yield from _ordered_simple_names(value)

        elif isinstance(value, list):
            yield value[0].simplified()

        else:
            assert False, value


def _taxonomy_listing():
    '''write out the names to a file'''
    have = set(load_known())
    everything = set(_ordered_simple_names(build_image_tree()))
    need = everything - have

    with open(root + 'data/taxonomy.txt', 'w+', encoding='utf8') as fd:
        for name in sorted(need):
            fd.write(name + '\n')


def _find_imprecise():
    '''find names with classifications that could be more specific'''
    names = all_names()
    m = mapping()

    for name in names:
        c = _to_classification(name, m)
        if ' sp.' in c:
            yield name


if not sys.flags.interactive and __name__ == '__main__':
    _taxonomy_listing()
