#!/usr/bin/python3

'''
parsing data from the file system to construct trees of images
'''

import os

from image import Image, categorize, split
from utility import flatten, tree_size, root
import static


def named():
    ''' all named images from all directories '''
    return flatten([[y for y in z if y.name] for z in _collect()])


def all_names():
    ''' all simplified, split names
    '''
    everything = {
        (categorize(split(i.simplified())), i)
        for i in _expand_names(named())
    }

    return {n for (n, _) in everything}


def single_level(tree):
    ''' squash the tree into a single level name to images dict
    '''
    assert isinstance(tree, dict), tree

    def inner(where):
        for value in where.values():
            if isinstance(value, list):
                yield value

            else:
                yield from inner(value)

    out = {}
    for group in inner(tree):
        name = group[0].simplified()

        out.setdefault(name, [])
        out[name] += group

    return out


def go():
    ''' construct a nested dictionary where each key is a unique split of a
    name (after processing) from right to left. if there's another split under
    this one, the value is another dictionary, otherwise, it's a list of Images
    '''
    return _data_to_various(
        _pruner(_compress(_compress(_make_tree(_expand_names(named())))))
    )


def find_vague_names():
    ''' find names that could be more specific

    import collections
    collections.Counter(i.simplified() for i in find_vague_names())
    '''
    everything = {
        (categorize(split(i.simplified())), i)
        for i in _expand_names(named())
    }

    names = {n for (n, _) in everything}

    for (name, image) in everything:
        for other in names:
            if name == other:
                continue

            if other.endswith(name):
                yield image


# PRIVATE

def _listing():
    """ a list of all dive picture folders available """
    return [d for d in os.listdir(root) if not d.startswith(".")]


def _delve(directory):
    """ create an Image object for each picture in a directory """
    path = os.path.join(root, directory)
    return [
        Image(o, directory)
        for o in os.listdir(path)
        if o.endswith(".jpg") and '-' in o
    ]


def _collect():
    """ run delve on all dive picture folders """
    return [_delve(d) for d in _listing()]


def _expand_names(images):
    """ split out `a and b` into separate elements """
    for image in images:
        for part in (" with ", " and "):
            if part not in image.name:
                continue

            left, right = image.name.split(part)

            clone = Image(image.label, image.directory)
            clone.name = left
            image.name = right
            yield clone

        yield image


def _make_tree(images):
    """ make a nested dictionary by words
    """
    out = {}

    for image in images:
        name = image.normalized()
        words = name.split(" ")[::-1]

        if words[0] in static.ignore:
            continue

        sub = out
        for word in words:
            sub.setdefault(word, {})
            sub = sub[word]

        sub.setdefault("data", [])
        sub["data"].append(image)

    return out


def _pruner(tree, too_few=5):
    """ remove top level keys with too few elements
    """
    to_remove = []

    for key, value in tree.items():
        if tree_size(value) <= too_few:
            to_remove.append(key)

    for remove in to_remove:
        # print('pruned', remove)
        tree.pop(remove)

    return tree


def _compress(tree):
    """ look for sub trees with no 'data' key, which can be squished up a level
    """
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):

        if not isinstance(value, dict):
            continue

        if "data" not in value and len(value.keys()) == 1:
            v = tree.pop(key)
            s = list(v.keys())[0]
            new_key = s + " " + key
            tree[new_key] = _compress(v[s])
        else:
            tree[key] = _compress(value)

    return tree


def _data_to_various(tree):
    ''' rebucket data into various
    '''
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if key == 'data':

            if len(tree.keys()) == 1:
                # we're alone, don't nest further
                continue

            values = tree.pop('data')
            assert 'various' not in tree
            tree['various'] = {'data': values}

        else:
            tree[key] = _data_to_various(value)

    return tree
