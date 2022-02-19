#!/usr/bin/python3

'''
dict and list functions
'''

import datetime
import os

root = "/mnt/zfs/Media/Pictures/Diving"
if os.name == 'nt':
    root = "Z:/Media/Pictures/Diving"


def take(xs, n):
    ''' pull n items from xs '''
    out = []
    count = 0
    for x in xs:
        if count == n:
            break
        count += 1
        out.append(x)
    return out


def flatten(xs):
    ''' [[a]] -> [a] '''
    return [item for sublist in xs for item in sublist]


def tree_size(tree):
    ''' number of leaves '''
    if not isinstance(tree, dict):
        return len(tree)

    return sum(tree_size(c) for c in tree.values())


def extract_leaves(tree):
    ''' get all the leaves in a tree of trees '''
    assert isinstance(tree, dict), tree

    for value in tree.values():
        if isinstance(value, dict):
            yield from extract_leaves(value)
        else:
            yield value


def extract_branches(tree):
    ''' get everything but the leaves '''
    assert isinstance(tree, dict), tree

    for key, value in tree.items():
        yield key
        if isinstance(value, dict):
            yield from extract_branches(value)


def hmap(arg, *fns):
    ''' apply all the functions provided to the argument, kind of like a fold
    '''
    out = arg
    for fn in fns:
        out = fn(out)
    return out


def is_date(x):
    ''' is this a date?
    '''
    try:
        d = datetime.datetime.strptime(x, '%Y-%m-%d')
        assert d or True  # pylint please
        return True
    except TypeError:
        return False
    except ValueError:
        return False


def strip_date(site):
    ''' remove the date from a string, unless it's only a date
    '''
    if ' ' not in site:
        return site

    *rest, last = site.split(' ')
    rest = ' '.join(rest)

    try:
        d = datetime.datetime.strptime(last, '%Y-%m-%d')
        assert d or True  # pylint please
    except ValueError:
        return site

    return rest


_EXISTS = dict()


def fast_exists(path):
    ''' cached os.path.exists
    '''
    if path in _EXISTS:
        return _EXISTS[path]

    exists = os.path.exists(path)
    _EXISTS[path] = exists
    return exists