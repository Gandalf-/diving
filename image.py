#!/usr/bin/python3

'''
base class for a diving image
'''

import hashlib
import os

import inflect
from apocrypha.client import Client

import utility
import static

database = Client()
inflect = inflect.engine()


def categorize(name):
    ''' add special categorization labels '''
    for category, values in static.categories.items():
        for value in values:
            if name.endswith(value):
                name += " " + category
    return name


def uncategorize(name):
    ''' remove the special categorization labels added earlier '''
    for category, values in static.categories.items():
        assert isinstance(values, list)

        for value in values:
            if name.endswith(" " + category) and value in name:
                name = name[:-len(' ' + category)]

    return name


def unqualify(name):
    ''' remove qualifiers '''
    for qualifier in static.qualifiers:
        if name.startswith(qualifier):
            name = name[len(qualifier) + 1 :]

    if name.endswith(' egg'):
        name, _ = name.split(' egg')

    if name.endswith(' eggs'):
        name, _ = name.split(' eggs')

    return name


def split(name):
    ''' add splits
    rockfish -> rock fish
    '''
    for s in static.splits:
        if name != s and name.endswith(s) and not name.endswith(" " + s):
            name = name.replace(s, " " + s)
    return name


def unsplit(name):
    ''' remove splits
    rock fish -> rockfish
    '''
    for s in static.splits:
        if name != s and name.endswith(' ' + s):
            name = name.replace(' ' + s, s)
    return name


class Image:
    ''' container for a diving picture '''

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

    def __repr__(self):
        return ", ".join(
            [
                # self.number,
                self.name,
                # self.directory
            ]
        )

    def location(self):
        ''' directory minus numbering
        '''
        when, where = self.directory.split(' ', 1)

        i = 0
        for i, l in enumerate(where):
            if l in '0123456789 ':
                continue
            break
        return when + ' ' + where[i:]

    def site(self):
        ''' directory minus numbering and date
        '''
        _, where = self.location().split(' ', 1)
        return where

    def identifier(self):
        ''' unique ID
        '''
        return self.directory + ':' + self.number

    def path(self):
        ''' where this is on the file system
        '''
        return os.path.join(utility.root, self.directory, self.label)

    def thumbnail(self):
        ''' what's the name of the thumbnail for this image?
        '''
        return self._hash() + '.jpg'

    def fullsize(self):
        ''' URI of full size image '''
        return "https://public.anardil.net/media/diving/{d}/{i}".format(
            d=self.directory, i=self.label,
        )

    def singular(self):
        ''' return singular version '''
        name = inflect.singular_noun(self.name.lower())
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
        ''' do we have a scientific name?
        names should be taxonomy.mapping()
        '''
        return names.get(self.simplified())

    def simplified(self):
        ''' remove qualifiers from name '''
        name = self.singular().lower()
        name = unqualify(name)

        return name

    def normalized(self):
        ''' lower case, remove plurals, split and expand '''
        # simplify name
        name = self.singular()
        name = split(name)
        name = categorize(name)

        return name

    def _hash(self):
        ''' hash a file the same way indexer does, so we can find it's thumbnail
        '''
        digest = database.get('diving', 'cache-hash', self.identifier())
        if digest:
            return digest

        sha1 = hashlib.sha1()

        with open(self.path(), "rb") as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha1.update(data)

        digest = sha1.hexdigest()
        database.set('diving', 'cache-hash', self.identifier(), value=digest)
        return digest
