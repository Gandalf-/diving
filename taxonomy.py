#!/usr/bin/python3

'''
taxonomy related things
'''

import sys
import pathlib
import yaml

from collection import go, single_level
from utility import extract_leaves

root = str(pathlib.Path(__file__).parent.absolute()) + '/'


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


def load_known():
    ''' load taxonomy.yml '''
    tree = load_tree()

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

        if isinstance(value, str):
            out[key] = value
            continue

        if len(value.keys()) == 1:
            # squash
            s = list(value.keys())[0]
            new_key = key + ' ' + s
            out[new_key] = compress(value[s])
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
            out[tree] = ' '.join(lineage)

        else:
            for key, value in tree.items():
                inner(value, out, lineage + [key])

    inner(tree, result)
    return result


def mapping():
    ''' simplified to scientific '''
    return invert_known(load_tree())


def taxonomy_listing():
    ''' write out the names to a file '''
    seen = set()
    known = set(load_known())

    with open(root + 'data/taxonomy.txt', 'w+') as fd:
        for name in ordered_simple_names(go()):
            if name in seen:
                continue
            seen.add(name)

            if name in known:
                print(name, 'done')
                continue

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
