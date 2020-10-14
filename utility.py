#!/usr/bin/python3

'''
dict and list functions
'''


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
