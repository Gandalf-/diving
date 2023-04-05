#!/usr/bin/python3

'''
dict and list functions
'''

import datetime
import os
from typing import List

root = "/mnt/zfs/Media/Pictures/Diving"
if os.name == 'nt':
    root = "Z:/Media/Pictures/Diving"
if os.uname().sysname == 'Darwin':
    root = "/Users/leaf/Pictures/Diving"

web_root = 'https://public.anardil.net/media/diving'


def titlecase(xs: str) -> str:
    '''xs.title() but a bit smarter'''
    return xs.title().replace("'S", "'s")


def sanitize_link(xs: str) -> str:
    '''cleanup names and lineages to links'''
    return xs.replace(' sp.', ' sp').replace(' ', '-').replace("'", '')


def prefix_tuples(first, ts):
    '''add a value to the beginning of each tuple in a list'''
    for (a, b) in ts:
        yield (first, a, b)


def take(xs, n):
    '''pull n items from xs'''
    result = []
    for i, x in enumerate(xs):
        if i == n:
            break
        result.append(x)
    return result


def walk_spine(tree, lineage: List[str]):
    '''walk the spine of a tree'''
    lineage = lineage[::-1]

    while lineage:
        vertebra = lineage.pop()
        assert vertebra in tree, tree.keys()
        tree = tree[vertebra]

    return tree


def flatten(xs):
    '''[[a]] -> [a]'''
    return [item for sublist in xs for item in sublist]


def tree_size(tree):
    '''number of leaves'''
    if not isinstance(tree, dict):
        return len(tree)

    return sum(tree_size(c) for c in tree.values())


def extract_leaves(tree):
    '''get all the leaves in a tree of trees'''
    assert isinstance(tree, dict), tree

    for value in tree.values():
        if isinstance(value, dict):
            yield from extract_leaves(value)
        elif isinstance(value, list):
            yield from value
        else:
            yield value


def extract_branches(tree):
    '''get everything but the leaves'''
    assert isinstance(tree, dict), tree

    for key, value in tree.items():
        yield key
        if isinstance(value, dict):
            yield from extract_branches(value)


def hmap(arg, *fns):
    '''apply all the functions provided to the argument, kind of like a fold'''
    out = arg
    for fn in fns:
        out = fn(out)
    return out


def is_date(x):
    '''is this a date?'''
    try:
        d = datetime.datetime.strptime(x, '%Y-%m-%d')
        assert d
        return True
    except (TypeError, ValueError):
        return False


def strip_date(site):
    '''remove the date from a string, unless it's only a date'''
    if ' ' not in site:
        return site

    *rest, last = site.split(' ')
    rest = ' '.join(rest)

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


_EXISTS = {}


def fast_exists(path):
    '''cached os.path.exists'''
    if path in _EXISTS:
        return _EXISTS[path]

    exists = os.path.exists(path)
    _EXISTS[path] = exists
    return exists
