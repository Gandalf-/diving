#!/usr/bin/python3

'''
collecting dive locations
'''

from util import collection
from util import static


def add_context(site):
    '''try to place a dive site into a larger collection of locations'''
    for name, places in static.locations.items():
        for place in places:
            if place == site:
                return ' '.join([name, site])

            if site.startswith(place):
                return ' '.join([name, site])

    return site


def sites():
    '''pruned, etc'''
    return collection.pipeline(_make_tree(), reverse=False)


# PRIVATE


def _make_tree():
    '''images organized into a nested dictionary where keys are locations'''
    images = collection.named()
    out = {}

    for image in images:
        when, *where = image.location().split(' ')
        where = ' '.join(where)
        where = add_context(where)

        words = where.split(' ')
        if words[-1] in static.ignore:
            continue

        sub = out
        for word in words:
            sub.setdefault(word, {})
            sub = sub[word]

        sub.setdefault(when, {})
        sub = sub[when]

        sub.setdefault("data", [])
        sub["data"].append(image)

    return out
