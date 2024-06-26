#!/usr/bin/python3

"""
collecting dive locations
"""

import re
from typing import List, cast

from util import collection, common, static
from util.collection import Image, ImageTree


def site_list() -> str:
    """join the location keys into a, b, c, and d"""
    *rest, last = list(sorted(static.locations.keys()))
    return ', '.join(rest) + f', and {last}'


def sites_link(when: str, where: str) -> str:
    """try to produce the correct /sites/ link"""
    site = add_context(where)
    link = common.sanitize_link(site)
    return f'/sites/{link}-{when}'


def get_region(site: str) -> str:
    """find a dive site in the larger collection of locations"""
    for name, places in static.locations.items():
        for place in places:
            if place == site:
                return name

            if site.startswith(place):
                return name

    assert False, f'no location for {site}'


def add_context(site: str) -> str:
    """place a dive site into a larger collection of locations"""
    return f'{get_region(site)} {site}'


def sites() -> ImageTree:
    """pruned, etc"""
    return collection.pipeline(_make_tree(), reverse=False)


def where_to_words(where: str) -> List[str]:
    """split the input into words but do not break up dive site names"""
    words = re.findall(_SITE_PATTERN, where)

    if len(words) > 1 and words[0] == 'British' and words[1] == 'Columbia':
        words = ['British Columbia'] + words[2:]

    return words


# PRIVATE


_SITE_PATTERN = re.compile(
    '|'.join(map(re.escape, common.extract_leaves(static.locations))) + '|\\S+'
)


def _make_tree() -> ImageTree:
    """images organized into a nested dictionary where keys are locations"""
    images = collection.named()
    out: ImageTree = {}

    for image in images:
        when, *where = image.location().split(' ')
        where = ' '.join(where)
        where = add_context(where) or where
        words = where_to_words(where)

        sub = out
        for word in words:
            sub.setdefault(word, {})
            sub = cast(ImageTree, sub[word])

        sub.setdefault(when, {})
        sub = cast(ImageTree, sub[when])

        sub.setdefault('data', [])
        cast(List[Image], sub['data']).append(image)

    return out
