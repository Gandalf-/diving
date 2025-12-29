#!/usr/bin/python3

"""
configuration information
"""

import glob
import hashlib
import os

from diving.util.metrics import metrics


class VersionedResource:
    """
    Wraps a file like style.css, returns the hashed content as the name, and
    can write out the file to the filesystem.

    This is useful for cache busting, so that we can set a long cache time on
    the resource, but still have it update when the content changes.
    """

    def __init__(self, path: str, target: str | None = None) -> None:
        self._name = os.path.basename(path)
        self._target = target or ''

        with open(path) as resource:
            self._body = resource.read()

        self._hash = hashlib.md5(self._body.encode('utf-8')).hexdigest()[:10]
        name, ext = os.path.splitext(self._name)
        self.path = os.path.join(self._target, f'{name}-{self._hash}{ext}')

        registry.append(self)

    def write(self) -> None:
        """write out the versioned resource"""
        if os.path.exists(self.path):
            return

        with open(self.path, 'w') as vr:
            vr.write(self._body)

    def versions(self) -> list[str]:
        """
        get all output versions of this resource, ordered by mtime, so that
        the newest version is first
        """
        name, ext = os.path.splitext(self._name)
        where = os.path.join(self._target, f'{name}-*{ext}')
        versions = glob.glob(where)

        def by_mtime(path: str) -> float:
            return os.stat(path).st_mtime

        return list(sorted(versions, key=by_mtime, reverse=True))

    def cleanup(self, count: int = 5) -> None:
        """remove all but the latest count versions of this resource"""
        for i, version in enumerate(self.versions()):
            if i >= count:
                metrics.counter('versioned resources deleted')
                os.remove(version)


registry: list[VersionedResource] = []
