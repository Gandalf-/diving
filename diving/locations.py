#!/usr/bin/python3

"""
collecting dive locations
"""

import os
from functools import lru_cache
from typing import Dict, List, Optional, Set, cast

from diving.util import collection, common, image, static
from diving.util.collection import Image, ImageTree


def site_list() -> str:
    """join the location keys into a, b, c, and d"""
    *rest, last = list(sorted(static.locations.keys()))
    return ', '.join(rest) + f', and {last}'


def sites_link(when: str, where: str) -> str:
    """try to produce the correct /sites/ link"""
    site = add_context(where)
    link = common.sanitize_link(site)
    return f'/sites/{link}-{when}'


def _find_location(site: str) -> tuple[str, Optional[str]] | None:
    """Find site in locations hierarchy, return (region, subregion) or None."""
    for region, value in static.locations.items():
        if isinstance(value, list):
            for place in value:
                if place == site or site.startswith(place):
                    return (region, None)
        else:
            for subregion, places in value.items():
                for place in places:
                    if place == site or site.startswith(place):
                        return (region, subregion)
    return None


def get_region(site: str) -> str:
    """find a dive site in the larger collection of locations"""
    result = _find_location(site)
    assert result, f'no location for {site}'
    return result[0]


def get_subregion(site: str) -> Optional[str]:
    """find a dive site's sub-region if it has one"""
    result = _find_location(site)
    return result[1] if result else None


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
    """Split location string into logical components using greedy tokenization"""
    multi_word_phrases = _get_multi_word_phrases()
    words = []
    remaining = where

    while remaining:
        remaining = remaining.lstrip()
        if not remaining:
            break

        matched = False

        # Try multi-word phrases first (longest to shortest)
        for phrase in multi_word_phrases:
            if remaining.startswith(phrase):
                # Ensure phrase is word-bounded (followed by space, end of string)
                next_char_idx = len(phrase)
                if next_char_idx >= len(remaining) or remaining[next_char_idx] == ' ':
                    words.append(phrase)
                    remaining = remaining[len(phrase) :]
                    matched = True
                    break

        # Fall back to single word
        if not matched:
            parts = remaining.split(' ', 1)
            words.append(parts[0])
            remaining = parts[1] if len(parts) > 1 else ''

    return words


def find_year_range(lineage: List[str]) -> str:
    """return a string like '2020, 2022-2024'"""
    region = ' '.join(lineage)
    return _pretty_year_range(_region_year_ranges()[region])


# PRIVATE


@lru_cache(None)
def _get_multi_word_phrases() -> List[str]:
    """Extract all multi-word phrases from locations hierarchy, sorted longest first"""
    phrases = []

    for region, value in static.locations.items():
        # Add multi-word region names
        if ' ' in region:
            phrases.append(region)

        if isinstance(value, list):
            # Flat structure: add multi-word site names
            for site in value:
                if ' ' in site:
                    phrases.append(site)
        else:
            # Nested structure: add sub-regions and sites
            for subregion, sites in value.items():
                if ' ' in subregion:
                    phrases.append(subregion)
                for site in sites:
                    if ' ' in site:
                        phrases.append(site)

    # Sort by length descending to match longest phrases first
    return sorted(set(phrases), key=len, reverse=True)


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
