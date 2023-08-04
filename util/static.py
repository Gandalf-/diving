#!/usr/bin/python3

'''
configuration information
'''

import os
import glob
import hashlib
from typing import Dict, List, Optional, Set

import yaml

from util.common import source_root
from util.metrics import metrics


ListTree = Dict[str, List[str]]

with open(source_root + 'data/static.yml') as fd:
    _static = yaml.safe_load(fd)

categories: ListTree = _static['categories']
difficulty: ListTree = _static['difficulty']
locations: ListTree = _static['locations']

pinned: Dict[str, str] = _static['pinned']

ignore: List[str] = _static['ignore']
splits: List[str] = _static['splits']
qualifiers: List[str] = _static['qualifiers']

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


class VersionedResource:
    '''
    Wraps a file like style.css, returns the hashed content as the name, and
    can write out the file to the filesystem.

    This is useful for cache busting, so that we can set a long cache time on
    the resource, but still have it update when the content changes.
    '''

    def __init__(self, path: str, target: Optional[str] = None) -> None:
        self._name = os.path.basename(path)
        self._target = target or ''

        with open(path) as resource:
            self._body = resource.read()

        self._hash = hashlib.md5(self._body.encode('utf-8')).hexdigest()[:10]
        name, ext = os.path.splitext(self._name)
        self.path = os.path.join(self._target, f'{name}-{self._hash}{ext}')

    def write(self) -> None:
        '''write out the versioned resource'''
        if os.path.exists(self.path):
            return

        with open(self.path, 'w') as vr:
            vr.write(self._body)

    def versions(self) -> List[str]:
        '''
        get all output versions of this resource, ordered by mtime, so that
        the newest version is first
        '''
        name, ext = os.path.splitext(self._name)
        where = os.path.join(self._target, f'{name}-*{ext}')
        versions = glob.glob(where)

        def by_mtime(path: str) -> float:
            return os.stat(path).st_mtime

        return list(sorted(versions, key=by_mtime, reverse=True))

    def cleanup(self, count: int = 5) -> None:
        '''remove all but the latest count versions of this resource'''
        for i, version in enumerate(self.versions()):
            if i >= count:
                metrics.counter('versioned resources deleted')
                os.remove(version)


stylesheet = VersionedResource(os.path.join(source_root, 'web/style.css'))
search_js = VersionedResource(os.path.join(source_root, 'web/search.js'))

search_data_path = 'search-data.js'
