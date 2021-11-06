#!/usr/bin/python3

'''
configuration information
'''

import pathlib
import yaml

_root = str(pathlib.Path(__file__).parent.absolute()) + '/'

with open(_root + 'data/static.yml') as fd:
    _static = yaml.safe_load(fd)

ignore = _static['ignore']
splits = _static['splits']
qualifiers = _static['qualifiers']
categories = _static['categories']
pinned = _static['pinned']
difficulty = _static['difficulty']
