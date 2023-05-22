#!/usr/bin/python3

'''
dict and list functions
'''

import datetime
import itertools
import functools
import os
import pathlib
from typing import List, Dict, Tuple, Any, Iterable, Callable

image_root = "/mnt/zfs/Media/Pictures/Diving"
if os.name == 'nt':
    image_root = "Z:/Media/Pictures/Diving"
if os.uname().sysname == 'Darwin':
    image_root = "/Users/leaf/Pictures/Diving"

source_root = str(pathlib.Path(__file__).parent.parent.absolute()) + '/'

Tree = Any


def titlecase(xs: str) -> str:
    '''xs.title() but a bit smarter'''
    return xs.title().replace("'S", "'s")


def sanitize_link(xs: str) -> str:
    '''cleanup names and lineages to links'''
    return xs.replace(' sp.', ' sp').replace(' ', '-').replace("'", '')


def prefix_tuples(
    first: Any, ts: List[Tuple[Any, Any]]
) -> Iterable[Tuple[Any, Any, Any]]:
    '''add a value to the beginning of each tuple in a list'''
    for a, b in ts:
        yield (first, a, b)


def take(xs: Iterable[Any], n: int) -> List[Any]:
    '''pull n items from xs'''
    return list(itertools.islice(xs, n))


def walk_spine(tree: Tree, lineage: List[str]) -> Tree:
    '''walk the spine of a tree'''
    lineage = lineage[::-1]

    while lineage:
        vertebra = lineage.pop()
        assert vertebra in tree, tree.keys()
        tree = tree[vertebra]

    return tree


def flatten(xs: List[List[Any]]) -> List[Any]:
    '''[[a]] -> [a]'''
    return [item for sublist in xs for item in sublist]


def tree_size(tree: Tree) -> int:
    '''number of leaves'''
    if not isinstance(tree, dict):
        return len(tree)

    return sum(tree_size(c) for c in tree.values())


def extract_leaves(tree: Tree) -> Iterable[Any]:
    '''get all the leaves in a tree of trees'''
    assert isinstance(tree, dict), tree

    for value in tree.values():
        if isinstance(value, dict):
            yield from extract_leaves(value)
        elif isinstance(value, list):
            yield from value
        else:
            yield value


def extract_branches(tree: Tree) -> Iterable[str]:
    '''get everything but the leaves'''
    assert isinstance(tree, dict), tree

    for key, value in tree.items():
        yield key
        if isinstance(value, dict):
            yield from extract_branches(value)


def hmap(arg: Any, *fns: Callable[[Any], Any]) -> Any:
    '''Apply a sequence of functions to an argument, returning the result.

    Example:
        >>> hmap(3, lambda x: x + 1, lambda x: x * 2)
        8
    '''
    return functools.reduce(lambda x, f: f(x), fns, arg)


def is_date(x: str) -> bool:
    '''is this a date?'''
    try:
        _ = datetime.datetime.strptime(x, '%Y-%m-%d')
        return True
    except (TypeError, ValueError):
        return False


def strip_date(site: str) -> str:
    '''Remove the date from a string, unless it's only a date.'''
    parts = site.split(' ')
    last = parts[-1]

    try:
        datetime.datetime.strptime(last, '%Y-%m-%d')
        return ' '.join(parts[:-1])
    except ValueError:
        return site


def pretty_date(when: str) -> str:
    date = datetime.datetime.strptime(when, '%Y-%m-%d')
    day_suffixes = {1: 'st', 2: 'nd', 3: 'rd'}

    if 4 <= date.day <= 20 or 24 <= date.day <= 30:
        suffix = 'th'
    else:
        suffix = day_suffixes[date.day % 10]

    return date.strftime(f'%B {date.day}{suffix}, %Y')


_EXISTS: Dict[str, bool] = {}


@functools.cache
def fast_exists(path: str) -> bool:
    '''cached os.path.exists'''
    if path in _EXISTS:
        return _EXISTS[path]

    return os.path.exists(path)
