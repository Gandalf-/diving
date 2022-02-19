#!/usr/bin/python3

'''
configuration information
'''

import pathlib
import yaml

_root = str(pathlib.Path(__file__).parent.absolute()) + '/'

with open(_root + '../data/static.yml') as fd:
    _static = yaml.safe_load(fd)

ignore = _static['ignore']
splits = _static['splits']
qualifiers = _static['qualifiers']
categories = _static['categories']
pinned = _static['pinned']
difficulty = _static['difficulty']
locations = _static['locations']


def _invert(tree):
    ''' map locations to full location names
    '''
    out = {}
    for area, places in tree.items():
        for place in places:
            out[place] = ' '.join([area, place])
    return out


location_map = _invert(locations)