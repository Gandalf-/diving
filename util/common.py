#!/usr/bin/python3

'''
dict and list functions
'''

import datetime
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
    result = []
    for i, x in enumerate(xs):
        if i == n:
            break
        result.append(x)
    return result


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
    '''apply all the functions provided to the argument, kind of like a fold'''
    out = arg
    for fn in fns:
        out = fn(out)
    return out


def is_date(x: str) -> bool:
    '''is this a date?'''
    try:
        d = datetime.datetime.strptime(x, '%Y-%m-%d')
        assert d
        return True
    except (TypeError, ValueError):
        return False


def strip_date(site: str) -> str:
    '''remove the date from a string, unless it's only a date'''
    if ' ' not in site:
        return site

    *parts, last = site.split(' ')
    rest = ' '.join(parts)

    try:
        d = datetime.datetime.strptime(last, '%Y-%m-%d')
        assert d
    except ValueError:
        return site

    return rest


def pretty_date(when: str) -> str:
    '''convert 2023-04-04 to April 4th, 2023'''
    year, month, day = when.split('-')

    day = day.lstrip('0')
    if day.endswith('1') and day != '11':
        day = f'{day}st'
    elif day.endswith('2') and day != '12':
        day = f'{day}nd'
    elif day.endswith('3') and day != '13':
        day = f'{day}rd'
    else:
        day = f'{day}th'

    month = {
        '1': 'January',
        '2': 'February',
        '3': 'March',
        '4': 'April',
        '5': 'May',
        '6': 'June',
        '7': 'July',
        '8': 'August',
        '9': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December',
    }[month.lstrip('0')]

    return f'{month} {day}, {year}'


_EXISTS: Dict[str, bool] = {}


@functools.cache
def fast_exists(path: str) -> bool:
    '''cached os.path.exists'''
    if path in _EXISTS:
        return _EXISTS[path]

    return os.path.exists(path)
