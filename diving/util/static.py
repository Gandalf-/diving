#!/usr/bin/python3
"""Configuration information."""

import os
import pathlib
from typing import TypeAlias

import yaml
from frozendict import frozendict

from diving.util.resource import VersionedResource

# Type alias for frozen nested location/category trees
FrozenListTree: TypeAlias = frozendict[str, tuple[str, ...] | frozendict[str, tuple[str, ...]]]

source_root = str(pathlib.Path(__file__).parent.parent.parent.absolute()) + '/'
image_root = '/Users/leaf/Pictures/Diving'

with open(source_root + 'data/static.yml') as fd:
    _static = yaml.safe_load(fd)


def _freeze_list_tree(tree: dict[str, list[str] | dict[str, list[str]]]) -> FrozenListTree:
    """Freeze a ListTree structure (dict with list or nested dict values)."""
    result: dict[str, tuple[str, ...] | frozendict[str, tuple[str, ...]]] = {}
    for key, value in tree.items():
        if isinstance(value, list):
            result[key] = tuple(value)
        else:
            result[key] = frozendict({k: tuple(v) for k, v in value.items()})
    return frozendict(result)


# Simple dicts -> frozendicts
dives: frozendict[int, str] = frozendict(_static['dives'])
pinned: frozendict[str, str] = frozendict(_static['pinned'])

# Lists -> tuples
dives_without_computer: tuple[str, ...] = tuple(_static['dives-without-computer'])
dives_without_camera: tuple[int, ...] = tuple(_static['dives-without-camera'])
ignore: tuple[str, ...] = tuple(_static['ignore'])
splits: tuple[str, ...] = tuple(_static['splits'])
qualifiers: tuple[str, ...] = tuple(_static['qualifiers'])
reef_organisms: tuple[str, ...] = tuple(_static['reef-organisms'])

# Sets -> frozensets
no_taxonomy_exact: frozenset[str] = frozenset(_static['no-taxonomy-exact'])
no_taxonomy_any: frozenset[str] = frozenset(_static['no-taxonomy-any'])

# Nested structures -> frozen trees
categories: FrozenListTree = _freeze_list_tree(_static['categories'])
difficulty: FrozenListTree = _freeze_list_tree(_static['difficulty'])
locations: FrozenListTree = _freeze_list_tree(_static['locations'])


def _invert(tree: FrozenListTree) -> frozendict[str, str]:
    """Map locations to full location names."""
    out: dict[str, str] = {}
    for area, value in tree.items():
        if isinstance(value, tuple):
            # Flat structure: region -> (sites)
            for place in value:
                out[place] = ' '.join([area, place])
        else:
            # Nested structure: region -> subregion -> (sites)
            for subregion, places in value.items():
                for place in places:
                    out[place] = ' '.join([area, subregion, place])
    return frozendict(out)


location_map: frozendict[str, str] = _invert(locations)

stylesheet = VersionedResource(os.path.join(source_root, 'web/style.css'))
search_js = VersionedResource(os.path.join(source_root, 'web/search.js'))
video_js = VersionedResource(os.path.join(source_root, 'web/video.js'))

timeline_js_path = os.path.join(source_root, 'web/timeline.js')
search_data_path = 'search-data.js'
