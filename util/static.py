#!/usr/bin/python3

'''
configuration information
'''

import os
import pathlib
from typing import Dict, List, Set

import yaml

from util.resource import VersionedResource

ListTree = Dict[str, List[str]]


source_root = str(pathlib.Path(__file__).parent.parent.absolute()) + '/'
image_root = "/Users/leaf/Pictures/Diving"

with open(source_root + 'data/static.yml') as fd:
    _static = yaml.safe_load(fd)

dives: Dict[int, str] = _static['dives']
dives_without_computer: List[str] = _static['dives-without-computer']
dives_without_camera: List[int] = _static['dives-without-camera']
categories: ListTree = _static['categories']
difficulty: ListTree = _static['difficulty']
locations: ListTree = _static['locations']

pinned: Dict[str, str] = _static['pinned']

ignore: List[str] = _static['ignore']
splits: List[str] = _static['splits']
qualifiers: List[str] = _static['qualifiers']
reef_organisms: List[str] = _static['reef-organisms']

no_taxonomy_exact: Set[str] = set(_static['no-taxonomy-exact'])
no_taxonomy_any: Set[str] = set(_static['no-taxonomy-any'])


def _invert(tree: Dict[str, List[str]]) -> Dict[str, str]:
    '''map locations to full location names'''
    out = {}
    for area, places in tree.items():
        for place in places:
            out[place] = ' '.join([area, place])
    return out


location_map = _invert(locations)

stylesheet = VersionedResource(os.path.join(source_root, 'web/style.css'))
search_js = VersionedResource(os.path.join(source_root, 'web/search.js'))

search_data_path = 'search-data.js'
