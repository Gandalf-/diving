#!/usr/bin/python3

"""
collecting dive locations
"""

import os
import re
from functools import lru_cache
from typing import Dict, List, Optional, Set, cast

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
    for name, value in static.locations.items():
        if isinstance(value, list):
            # Flat structure: region -> [sites]
            for place in value:
                if place == site:
                    return name

                if site.startswith(place):
                    return name
        else:
            # Nested structure: region -> subregion -> [sites]
            for subregion, places in value.items():
                for place in places:
                    if place == site:
                        return name

                    if site.startswith(place):
                        return name

    assert False, f'no location for {site}'


def get_subregion(site: str) -> Optional[str]:
    """find a dive site's sub-region if it has one"""
    for name, value in static.locations.items():
        if isinstance(value, dict):
            # Nested structure: region -> subregion -> [sites]
            for subregion, places in value.items():
                for place in places:
                    if place == site or site.startswith(place):
                        return subregion
    return None


def add_context(site: str) -> str:
    """place a dive site into a larger collection of locations"""
    region = get_region(site)
    subregion = get_subregion(site)

    if subregion:
        return f'{region} {subregion} {site}'
    else:
        return f'{region} {site}'


def sites() -> ImageTree:
    """pruned, etc"""
    return collection.pipeline(_make_tree(), reverse=False)


def where_to_words(where: str) -> List[str]:
    """split the input into words but do not break up dive site names"""
    # Pre-process multi-word patterns before regex splitting
    where = where.replace('Queen Charlotte Strait', 'Queen-Charlotte-Strait')
    where = where.replace('Jervis Inlet', 'Jervis-Inlet')

    words = re.findall(_SITE_PATTERN, where)

    if len(words) > 1 and words[0] == 'British' and words[1] == 'Columbia':
        words = ['British Columbia'] + words[2:]

    # Restore multi-word patterns
    words = [w.replace('Queen-Charlotte-Strait', 'Queen Charlotte Strait') for w in words]
    words = [w.replace('Jervis-Inlet', 'Jervis Inlet') for w in words]

    return words


def find_year_range(lineage: List[str]) -> str:
    """return a string like '2020, 2022-2024'"""
    region = ' '.join(lineage)
    return _pretty_year_range(_region_year_ranges()[region])


# PRIVATE


@lru_cache(None)
def _region_year_ranges() -> Dict[str, Set[int]]:
    out: Dict[str, Set[int]] = {}

    for path in collection.dive_listing():
        dive = os.path.basename(path)

        year, *_ = dive.split('-')
        year = int(year)

        where = image.dive_to_location(dive)
        where = add_context(where)

        parts = where_to_words(where)
        for i, part in enumerate(parts):
            region = ' '.join(parts[: i + 1])
            out.setdefault(region, set())
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
