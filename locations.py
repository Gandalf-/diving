#!/usr/bin/python3

'''
collecting dive locations
'''

from typing import Optional

from util import collection
from util import static
from util import common

from util.collection import ImageTree


def site_list() -> str:
    '''join the location keys into a, b, c, and d'''
    *rest, last = list(sorted(static.locations.keys()))
    return ', '.join(rest) + f', and {last}'


def sites_link(when: str, where: str) -> Optional[str]:
    '''try to produce the correct /sites/ link'''
    site = add_context(where)
    link = common.sanitize_link(site)
    url = f'sites/{link}-{when}.html'

    if common.fast_exists(url):
        return f'/{url}'

    return None


def get_context(site: str) -> Optional[str]:
    '''try to find a dive site in the larger collection of locations'''
    for name, places in static.locations.items():
        for place in places:
            if place == site:
                return name

            if site.startswith(place):
                return name

    return None


def add_context(site: str) -> str:
    '''try to place a dive site into a larger collection of locations'''
    name = get_context(site)
    if name:
        return ' '.join([name, site])

    return site


def sites() -> ImageTree:
    '''pruned, etc'''
    return collection.pipeline(_make_tree(), reverse=False)


# PRIVATE


def _make_tree() -> ImageTree:
    '''images organized into a nested dictionary where keys are locations'''
    images = collection.named()
    out: ImageTree = {}

    for image in images:
        when, *where = image.location().split(' ')
        where = ' '.join(where)
        where = add_context(where) or where

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
