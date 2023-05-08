#!/usr/bin/python3

'''
parsing data from the file system to construct trees of images
'''

import os
from typing import Iterable, Set, Dict, List, Iterator

from util.image import Image, categorize, split
from util.common import flatten, tree_size, image_root, Tree
from util import static

ImageTree = Tree


def named() -> List[Image]:
    '''all named images from all directories'''
    return flatten([[y for y in z if y.name] for z in _collect_all_images()])


def all_names() -> Set[str]:
    '''all simplified, split names'''
    return {categorize(split(i.simplified())) for i in expand_names(named())}


def single_level(tree: ImageTree) -> Dict[str, List[Image]]:
    '''squash the tree into a single level name to images dict'''
    assert isinstance(tree, dict), tree

    def inner(where: ImageTree) -> Iterator[List[Image]]:
        for value in where.values():
            if isinstance(value, list):
                yield value
            else:
                yield from inner(value)

    out: Dict[str, List[Image]] = {}
    for group in inner(tree):
        name = group[0].simplified()

        out.setdefault(name, [])
        out[name] += group

    return out


def build_image_tree() -> ImageTree:
    '''construct a nested dictionary where each key is a unique split of a
    name (after processing) from right to left. if there's another split under
    this one, the value is another dictionary, otherwise, it's a list of Images
    '''
    return pipeline(_make_tree(expand_names(named())))


def pipeline(tree: ImageTree, reverse: bool = True) -> ImageTree:
    '''intermediate steps!'''
    return _data_to_various(
        _pruner(_compress(_compress(_compress(tree, reverse), reverse), reverse))
    )


def delve(dive_path: str) -> List[Image]:
    '''
    Create an Image object for each labeled picture in a directory; the path
    provided must be absolute
    '''
    directory = os.path.basename(dive_path)
    return [
        Image(entry, directory)
        for entry in os.listdir(dive_path)
        if entry.endswith(".jpg") and '-' in entry
    ]


def expand_names(images: List[Image]) -> Iterator[Image]:
    """split out `a and b` into separate elements"""
    for image in images:
        for part in (" with ", " and "):
            if part not in image.name:
                continue

            left, right = image.name.split(part)
            lnew = Image(image.label, image.directory)
            rnew = Image(image.label, image.directory)
            lnew.name = left
            rnew.name = right
            yield lnew
            yield rnew
            break
        else:
            yield image


def dive_listing() -> List[str]:
    """a list of all dive picture folders available"""
    return [
        os.path.join(image_root, dive)
        for dive in os.listdir(image_root)
        if not dive.startswith(".")
    ]


# PRIVATE


def _collect_all_images() -> List[List[Image]]:
    """run delve on all dive picture folders"""
    return [delve(dive_path) for dive_path in dive_listing()]


def _make_tree(images: Iterable[Image]) -> ImageTree:
    """make a nested dictionary by words"""
    out: ImageTree = {}

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


def _pruner(tree: ImageTree, too_few: int = 5) -> ImageTree:
    """remove top level keys with too few elements"""
    to_remove = []

    for key, value in tree.items():
        if tree_size(value) <= too_few:
            to_remove.append(key)

    for remove in to_remove:
        # print('pruned', remove)
        tree.pop(remove)

    return tree


def _compress(tree: ImageTree, reverse: bool = True) -> ImageTree:
    """look for sub trees with no 'data' key, which can be squished up a level"""
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if not isinstance(value, dict):
            continue

        if "data" not in value and len(value.keys()) == 1:
            v = tree.pop(key)
            s = list(v.keys())[0]

            if reverse:
                new_key = s + " " + key
            else:
                new_key = key + " " + s

            tree[new_key] = _compress(v[s], reverse)
        else:
            tree[key] = _compress(value, reverse)

    return tree


def _data_to_various(tree: ImageTree) -> ImageTree:
    '''rebucket data into various'''
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
