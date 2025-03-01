#!/usr/bin/python3

"""
collecting dive locations
"""

import os
import re
from functools import lru_cache
from typing import Dict, List, Set, cast

from util import collection, common, image, static
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


def region_to_year_range(lineage: List[str]) -> str:
    """return a string like '2020, 2022-2024'"""
    region = lineage[0]
    return _pretty_year_range(_region_year_ranges()[region])


# PRIVATE


@lru_cache(None)
def _region_year_ranges() -> Dict[str, Set[int]]:
    out: Dict[str, Set[int]] = {k: set() for k in static.locations.keys()}

    for path in collection.dive_listing():
        dive = os.path.basename(path)
        year, *_ = dive.split('-')
        year = int(year)

        site = image.dive_to_site(dive)

        region = get_region(site)
        out[region].add(year)

    return out


def _pretty_year_range(years: Set[int]) -> str:
    """1, 3, 4, 6 -> 1, 3-4, 6"""
    out = []
    years = sorted(list(years))

    while years:
        start = years.pop(0)
        end = start

        while years and years[0] == end + 1:
            end = years.pop(0)

        if start == end:
            out.append(str(start))
        else:
            out.append(f'{start}-{end}')

    return ', '.join(out)


_SITE_PATTERN = re.compile(
    '|'.join(map(re.escape, common.extract_leaves(static.locations))) + '|\\S+'
)


def _make_tree() -> ImageTree:
    """images organized into a nested dictionary where keys are locations"""
    images = collection.named()
    out: ImageTree = {}

    for image_ in images:
        when, *where = image_.location().split(' ')
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
        cast(List[Image], sub['data']).append(image_)

    return out
