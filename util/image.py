#!/usr/bin/python3

'''
base class for a diving image
'''

import os
from typing import Optional, cast

import inflect

from util import database
from util.common import image_root, Tree

from util import static

_inflect = inflect.engine()


def categorize(name: str) -> str:
    '''add special categorization labels'''
    for category, values in static.categories.items():
        for value in values:
            if name.endswith(value):
                name += f' {category}'
    return name


def uncategorize(name: str) -> str:
    '''remove the special categorization labels added earlier'''
    for category, values in static.categories.items():
        assert isinstance(values, list)

        for value in values:
            if name.endswith(f' {category}') and value in name:
                name = name[: -len(f' {category}')]

    return name


def unqualify(name: str) -> str:
    '''remove qualifiers'''
    for qualifier in static.qualifiers:
        if name.startswith(qualifier):
            name = name[len(qualifier) + 1 :]

    if name.endswith(' egg'):
        name, _ = name.split(' egg')

    if name.endswith(' eggs'):
        name, _ = name.split(' eggs')

    return name


def split(name: str) -> str:
    '''add splits
    rockfish -> rock fish
    '''
    for s in static.splits:
        if name != s and name.endswith(s) and not name.endswith(" " + s):
            name = name.replace(s, " " + s)
    return name


def unsplit(name: str) -> str:
    '''remove splits
    rock fish -> rockfish
    '''
    for s in static.splits:
        if name != s and name.endswith(' ' + s):
            name = name.replace(' ' + s, s)
    return name


class Image:
    '''container for a diving picture'''

    def __init__(self, label: str, directory: str) -> None:
        self.label = label
        label, _ = os.path.splitext(label)

        if " - " in label:
            number, name = label.split(" - ")
        else:
            number = label
            name = ""

        self.name = name
        self.number = number
        self.directory = directory
        self.database = database.database

    def __repr__(self) -> str:
        return self.name

    def location(self) -> str:
        '''directory minus numbering'''
        when, where = self.directory.split(' ', 1)

        i = 0
        for i, char in enumerate(where):
            if char in '0123456789 ':
                continue
            break
        return when + ' ' + where[i:]

    def site(self) -> str:
        '''directory minus numbering and date'''
        _, where = self.location().split(' ', 1)
        return where

    def identifier(self) -> str:
        '''unique ID'''
        return self.directory + ':' + self.number

    def path(self) -> str:
        '''where this is on the file system'''
        return os.path.join(image_root, self.directory, self.label)

    def thumbnail(self) -> str:
        '''URI of thumbnail image'''
        return f'/imgs/{self.hashed()}.webp'

    def fullsize(self) -> str:
        '''URI of original image'''
        return f'/full/{self.hashed()}.webp'

    def hashed(self) -> str:
        '''Get the sha1sum for an original image, using the database as a
        cache'''
        sha1 = self.database.get_image_hash(self.identifier())
        assert sha1, f'{self.directory}/{self.label} has no hash'
        return sha1

    def singular(self) -> str:
        '''return singular version'''
        assert self.name, self

        singular = _inflect.singular_noun(self.name.lower())
        name = cast(str, singular) if singular else self.name.lower()

        # fix inflect's mistakes
        for tofix in ("octopu", "gras", "fuscu", "dori"):
            if tofix + "s" in name:
                continue
            if name.endswith(tofix) or tofix + " " in name:
                name = name.replace(tofix, tofix + "s")

        if name.endswith("alga"):
            name += "e"

        return name

    def scientific(self, names: Tree) -> Optional[str]:
        '''do we have a scientific name?
        names should be taxonomy.mapping()
        '''
        return names.get(self.simplified())

    def simplified(self) -> str:
        '''remove qualifiers from name'''
        return unqualify(self.singular())

    def normalized(self) -> str:
        '''lower case, remove plurals, split and expand'''
        # simplify name
        name = self.singular()
        name = split(name)
        name = categorize(name)

        return name
