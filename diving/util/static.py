#!/usr/bin/python3

"""
configuration information
"""

import os
import pathlib

import yaml

from diving.util.resource import VersionedResource

ListTree = dict[str, list[str] | dict[str, list[str]]]


source_root = str(pathlib.Path(__file__).parent.parent.parent.absolute()) + '/'
image_root = '/Users/leaf/Pictures/Diving'

with open(source_root + 'data/static.yml') as fd:
    _static = yaml.safe_load(fd)

dives: dict[int, str] = _static['dives']
dives_without_computer: list[str] = _static['dives-without-computer']
dives_without_camera: list[int] = _static['dives-without-camera']
categories: ListTree = _static['categories']
difficulty: ListTree = _static['difficulty']
locations: ListTree = _static['locations']

pinned: dict[str, str] = _static['pinned']

ignore: list[str] = _static['ignore']
splits: list[str] = _static['splits']
qualifiers: list[str] = _static['qualifiers']
reef_organisms: list[str] = _static['reef-organisms']

no_taxonomy_exact: set[str] = set(_static['no-taxonomy-exact'])
no_taxonomy_any: set[str] = set(_static['no-taxonomy-any'])


def _invert(tree: ListTree) -> dict[str, str]:
    """map locations to full location names"""
    out = {}
    for area, value in tree.items():
        if isinstance(value, list):
            # Flat structure: region -> [sites]
            for place in value:
                out[place] = ' '.join([area, place])
        else:
            # Nested structure: region -> subregion -> [sites]
            for subregion, places in value.items():
                for place in places:
                    out[place] = ' '.join([area, subregion, place])
    return out


location_map = _invert(locations)

stylesheet = VersionedResource(os.path.join(source_root, 'web/style.css'))
search_js = VersionedResource(os.path.join(source_root, 'web/search.js'))
video_js = VersionedResource(os.path.join(source_root, 'web/video.js'))

timeline_js_path = os.path.join(source_root, 'web/timeline.js')
search_data_path = 'search-data.js'
