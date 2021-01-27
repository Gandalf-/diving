#!/usr/bin/python3

'''
taxonomy related things
'''

import enum
import sys
import pathlib
import yaml

from collection import go, single_level
from utility import extract_leaves

root = str(pathlib.Path(__file__).parent.absolute()) + '/'


def simplify(name: str) -> str:
    ''' try to use similar() to simplify the lineage
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
    ''' determine if two words are similar, usually a super family and family,
    or something to that effect
    '''
    length = sum([len(a), len(b)]) // 2
    pivot = int(length * 0.5)

    return a[:pivot] == b[:pivot]


def ordered_simple_names(tree):
    ''' taxonomy names '''
    assert isinstance(tree, dict), tree

    for value in tree.values():
        if isinstance(value, dict):
            yield from ordered_simple_names(value)

        elif isinstance(value, list):
            yield value[0].simplified()

        else:
            assert False, value


def load_tree():
    ''' yaml load '''
    with open(root + 'data/taxonomy.yml') as fd:
        return yaml.load(fd)


def filter_exact(tree):
    ''' remove all sp entries
    '''
    assert isinstance(tree, dict), tree

    out = {}
    for key, value in tree.items():
        if key == 'sp':
            continue

        if isinstance(value, dict):
            out[key] = filter_exact(value)
        else:
            out[key] = value

    return out


def load_known(exact_only=False):
    ''' load taxonomy.yml '''

    tree = load_tree()
    if exact_only:
        tree = filter_exact(tree)

    for leaf in extract_leaves(tree):
        yield from leaf.split(', ')


def full_compress(tree):
    ''' keep compressing until nothing changes '''
    old = tree

    while True:
        new = compress(old)
        if new == old:
            break
        old = new

    return new


def compress(tree):
    ''' squash levels '''

    if isinstance(tree, str):
        # hit a leaf
        return tree

    out = {}

    for key, value in list(tree.items()):

        if key == 'sp':
            continue

        if isinstance(value, str):
            out[key] = value
            continue

        if len(value.keys()) == 1:
            child = list(value.keys())[0]

            # squash
            new_key = key + ' ' + child
            out[new_key] = compress(value[child])
        else:
            out[key] = compress(value)

    return out


def invert_known(tree):
    ''' leaves become roots '''

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


MappingType = enum.Enum('MappingType', 'Gallery Taxonomy')


def mapping(where=MappingType.Gallery):
    ''' simplified to scientific '''
    tree = invert_known(load_tree())

    if where == MappingType.Gallery:
        return tree

    return {v.replace(' sp', ''): k for k, v in tree.items()}


def taxonomy_listing():
    ''' write out the names to a file '''
    have = set(load_known())
    everything = set(ordered_simple_names(go()))
    need = everything - have

    with open(root + 'data/taxonomy.txt', 'w+') as fd:
        for name in sorted(need):
            fd.write(name + '\n')


def taxia_filler(tree, images):
    ''' fill in the images
    '''
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if isinstance(value, str):
            if value in images:
                tree[key] = {'data': images[value]}

            else:
                print('dropping', key)
                tree.pop(key)
        else:
            tree[key] = taxia_filler(value, images)

    return tree


def gallery_tree(tree=None):
    ''' produce a tree for gallery.py to use
    the provided tree must be from collection.go()
    '''
    if not tree:
        tree = go()

    images = single_level(tree)
    taxia = full_compress(load_tree())

    taxia_filler(taxia, images)

    return taxia


if not sys.flags.interactive and __name__ == '__main__':
    taxonomy_listing()
