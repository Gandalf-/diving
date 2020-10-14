#!/usr/bin/python3

'''
taxonomy related things
'''

import pathlib
import yaml

from collection import go
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


if __name__ == '__main__':
    taxonomy_listing()
