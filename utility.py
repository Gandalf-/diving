#!/usr/bin/python3

'''
dict and list functions
'''


root = "/mnt/zfs/Media/Pictures/Diving"


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
