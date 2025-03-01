#!/usr/bin/python3

"""
base class for a diving image
"""

import os
from functools import lru_cache
from typing import List, Optional, Tuple

from util import database, log, static
from util.common import Tree
from util.grammar import singular


def dive_to_location(dive: str) -> str:
    _, where = dive.split(' ', 1)

    i = 0
    for i, char in enumerate(where):
        if char in '0123456789 ':
            continue
        break

    return where[i:]


def categorize(name: str) -> str:
    """add special categorization labels"""
    for category, values in static.categories.items():
        for value in values:
            if name.endswith(value):
                name += f' {category}'
    return name


def uncategorize(name: str) -> str:
    """remove the special categorization labels added earlier"""
    for category, values in static.categories.items():
        assert isinstance(values, list)

        for value in values:
            if name.endswith(f' {category}') and value in name:
                name = name[: -len(f' {category}')]

    return name


def unqualify(name: str) -> str:
    """remove qualifiers"""
    for qualifier in static.qualifiers:
        if name.startswith(qualifier):
            name = name[len(qualifier) + 1 :]

    if name.endswith(' egg'):
        name, _ = name.split(' egg')

    if name.endswith(' eggs'):
        name, _ = name.split(' eggs')

    return name


def split(name: str) -> str:
    """add splits
    rockfish -> rock fish
    """
    for s in static.splits:
        if name != s and name.endswith(s) and not name.endswith(' ' + s):
            name = name.replace(s, ' ' + s)
    return name


def unsplit(name: str) -> str:
    """remove splits
    rock fish -> rockfish
    """
    for s in static.splits:
        if name != s and name.endswith(' ' + s):
            name = name.replace(' ' + s, s)
    return name


class Image:
    """container for a diving picture"""

    def __init__(self, label: str, directory: str, position: float = 0.0) -> None:
        self.label = label
        label, ext = os.path.splitext(label)

        if ' - ' in label:
            number, name = label.split(' - ')
        else:
            number = label
            name = ''

        self.name = name
        self.number = number
        self.directory = directory
        self.position = position
        self.database = database.database
        self.is_image = ext == '.jpg'
        self.is_video = ext in (
            '.mov',
            '.mp4',
        )

    def __repr__(self) -> str:
        return self.name

    def location(self) -> str:
        """directory minus numbering"""
        when, _ = self.directory.split(' ', 1)
        where = dive_to_location(self.directory)

        return f'{when} {where}'

    def site(self) -> str:
        """directory minus numbering and date"""
        _, where = self.location().split(' ', 1)
        return where

    def identifier(self) -> str:
        """unique ID"""
        return self.directory + ':' + self.number

    def path(self) -> str:
        """where this is on the file system"""
        return os.path.join(static.image_root, self.directory, self.label)

    def thumbnail(self) -> str:
        """URI of thumbnail image"""
        if self.is_video:
            return f'/clips/{self.hashed()}.mp4'
        return f'/imgs/{self.hashed()}.webp'

    def fullsize(self) -> str:
        """URI of original image"""
        if self.is_video:
            return f'/video/{self.hashed()}.mp4'
        return f'/full/{self.hashed()}.webp'

    def hashed(self) -> str:
        """Get the sha1sum for an original image, using the database as a
        cache"""
        sha1 = self.database.get_image_hash(self.identifier())
        assert sha1, f'{self.directory}/{self.label} has no hash'
        return sha1

    def singular(self) -> str:
        """return singular version"""
        assert self.name, self
        return singular(self.name)

    def scientific(self, names: Tree) -> Optional[str]:
        """do we have a scientific name?
        names should be taxonomy.mapping()
        """
        return names.get(self.simplified())

    def simplified(self) -> str:
        """remove qualifiers from name"""
        return unqualify(self.singular())

    def normalized(self) -> str:
        """lower case, remove plurals, split and expand"""
        # simplify name
        name = self.singular()
        name = split(name)
        name = categorize(name)
        return name

    @lru_cache(None)
    def approximate_depth(self) -> Optional[Tuple[int, int]]:
        """approximate depth of this image"""
        info = log.lookup(self.directory)
        if not info or not info['depths']:
            return None

        depths = info['depths']
        before = _depth_at(depths, max(self.position * 0.9, 0.0))
        exact = _depth_at(depths, self.position)
        after = _depth_at(depths, min(self.position * 1.1, 1.0))

        return (min(before, exact, after), max(before, exact, after))


# PRIVATE


def _depth_at(depths: List[Tuple[float, int]], position: float) -> int:
    for index, depth in depths:
        if index >= position:
            return depth
    assert False
