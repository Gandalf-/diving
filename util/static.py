#!/usr/bin/python3

'''
configuration information
'''

from typing import Dict, List

import yaml

from util.common import source_root


with open(source_root + 'data/static.yml') as fd:
    _static = yaml.safe_load(fd)

ignore: List[str] = _static['ignore']
splits: List[str] = _static['splits']
qualifiers: List[str] = _static['qualifiers']
categories: Dict[str, List[str]] = _static['categories']
pinned: Dict[str, str] = _static['pinned']
difficulty: Dict[str, List[str]] = _static['difficulty']
locations: Dict[str, List[str]] = _static['locations']


def _invert(tree: Dict[str, List[str]]) -> Dict[str, str]:
    '''map locations to full location names'''
    out = {}
    for area, places in tree.items():
        for place in places:
            out[place] = ' '.join([area, place])
    return out


location_map = _invert(locations)
