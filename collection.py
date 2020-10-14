#!/usr/bin/python3

'''
parsing data from disk
'''

import os

from image import Image
from utility import flatten, tree_size


root = "/mnt/zfs/Media/Pictures/Diving"


def listing():
    """ a list of all dive picture folders available """
    return [d for d in os.listdir(root) if not d.startswith(".")]


def delve(directory):
    """ create an Image object for each picture in a directory """
    path = os.path.join(root, directory)
    return [
        Image(o, directory) for o in os.listdir(path) if o.endswith(".jpg")
    ]


def collect():
    """ run delve on all dive picture folders """
    return [delve(d) for d in listing()]


def named():
    ''' all named images from all directories '''
    return flatten([[y for y in z if y.name] for z in collect()])


def expand_names(images):
    """ split out `a and b` into separate elements """
    result = []

    for image in images:
        for split in (" with ", " and "):

            if split not in image.name:
                continue

            left, right = image.name.split(split)

            clone = Image(image.label, image.directory)
            clone.name = left
            image.name = right
            result.append(clone)

        result.append(image)

    return result


def make_tree(images):
    """ make a nested dictionary by words
    """
    ignore = ('pier', 'rock')
    out = {}

    for image in images:
        name = image.normalized()
        words = name.split(" ")[::-1]

        if words[0] in ignore:
            continue

        sub = out
        for word in words:
            sub.setdefault(word, {})
            sub = sub[word]

        sub.setdefault("data", [])
        sub["data"].append(image)

    return out


def pruner(tree, too_few=5):
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


def compress(tree):
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
            tree[new_key] = compress(v[s])
        else:
            tree[key] = compress(value)

    return tree


def data_to_various(tree):
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
            tree[key] = data_to_various(value)

    return tree


def go():
    ''' full pipeline '''
    return data_to_various(
        pruner(compress(compress(make_tree(expand_names(named())))))
    )
