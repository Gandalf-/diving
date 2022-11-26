#!/usr/bin/python3

'''
base class for a diving image
'''

import os

import inflect

from util import database
import util.common as utility

from util import static

_inflect = inflect.engine()


def categorize(name):
    '''add special categorization labels'''
    for category, values in static.categories.items():
        for value in values:
            if name.endswith(value):
                name += " " + category
    return name


def uncategorize(name):
    '''remove the special categorization labels added earlier'''
    for category, values in static.categories.items():
        assert isinstance(values, list)

        for value in values:
            if name.endswith(" " + category) and value in name:
                name = name[: -len(' ' + category)]

    return name


def unqualify(name):
    '''remove qualifiers'''
    for qualifier in static.qualifiers:
        if name.startswith(qualifier):
            name = name[len(qualifier) + 1 :]

    if name.endswith(' egg'):
        name, _ = name.split(' egg')

    if name.endswith(' eggs'):
        name, _ = name.split(' eggs')

    return name


def split(name):
    '''add splits
    rockfish -> rock fish
    '''
    for s in static.splits:
        if name != s and name.endswith(s) and not name.endswith(" " + s):
            name = name.replace(s, " " + s)
    return name


def unsplit(name):
    '''remove splits
    rock fish -> rockfish
    '''
    for s in static.splits:
        if name != s and name.endswith(' ' + s):
            name = name.replace(' ' + s, s)
    return name


class Image:
    '''container for a diving picture'''

    def __init__(self, label, directory):
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

    def __repr__(self):
        return ", ".join(
            [
                # self.number,
                self.name,
                # self.directory
            ]
        )

    def location(self):
        '''directory minus numbering'''
        when, where = self.directory.split(' ', 1)

        i = 0
        for i, l in enumerate(where):
            if l in '0123456789 ':
                continue
            break
        return when + ' ' + where[i:]

    def site(self):
        '''directory minus numbering and date'''
        _, where = self.location().split(' ', 1)
        return where

    def identifier(self):
        '''unique ID'''
        return self.directory + ':' + self.number

    def path(self):
        '''where this is on the file system'''
        return os.path.join(utility.root, self.directory, self.label)

    def thumbnail(self):
        '''URI of thumbnail image'''
        sha1 = self.hashed()
        assert sha1
        return '/imgs/' + sha1 + '.jpg'

    def fullsize(self):
        '''URI of original image'''
        sha1 = self.hashed()
        assert sha1
        return '/full/' + sha1 + '.jpg'

    def hashed(self) -> str:
        '''Get the sha1sum for an original image, using the database as a cache'''
        return self.database.get('diving', 'cache', self.identifier(), 'hash')

    def singular(self):
        '''return singular version'''
        assert self.name, self

        name = _inflect.singular_noun(self.name.lower())
        name = name or self.name.lower()

        # fix inflect's mistakes
        for tofix in ("octopu", "gras", "fuscu", "dori"):
            if tofix + "s" in name:
                continue
            if name.endswith(tofix) or tofix + " " in name:
                name = name.replace(tofix, tofix + "s")

        if name.endswith("alga"):
            name += "e"

        return name

    def scientific(self, names):
        '''do we have a scientific name?
        names should be taxonomy.mapping()
        '''
        return names.get(self.simplified())

    def simplified(self):
        '''remove qualifiers from name'''
        return unqualify(self.singular())

    def normalized(self):
        '''lower case, remove plurals, split and expand'''
        # simplify name
        name = self.singular()
        name = split(name)
        name = categorize(name)

        return name
