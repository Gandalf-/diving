#!/usr/bin/python3

'''
base class for a diving image
'''

import hashlib
import os

import inflect
import utility

inflect = inflect.engine()

splits = ("fish", "coral", "ray")

qualifiers = (
    'juvenile',
    'dying',
    'dead',
    'female',
    'male',
    'molted',
    'fighting',
    'pregnant',
    'mating',
    'elderly',
    'wasting',
    'cleaning',
    'school of',
    'husk of',
    'swimming',
    'sleeping',
    'rebreather',
    'various',
)

categories = {
    "fish": (
        "basslet",
        "blue tang",
        "flounder",
        "cero",
        "goby",
        "greenling",
        "grunt",
        "gunnel",
        "grouper",
        "lingcod",
        "midshipman",
        "perch",
        "rock beauty",
        "sculpin",
        "sculpin",
        "sole",
        "sardine",
        "spotted drum",
        "tarpon",
        "tomtate",
        "war bonnet",
    ),
    "shrimp": ("prawn", ),
    "algae": ("kelp", "seagrass", ),
    "crab": ("reef spider",),
    "nudibranch": ("sea lemon", "dorid", "dendronotid"),
    "anemone": ("zoanthid",),
    "tunicate": ("sea squirt", ),
    "coral": ("sea pen", "sea whip", "sea rod"),
}


def categorize(name):
    ''' add special categorization labels '''
    for category, values in categories.items():
        for value in values:
            if name.endswith(value):
                name += " " + category
    return name


def uncategorize(name):
    ''' remove the special categorization labels added earlier '''
    for category, values in categories.items():
        assert isinstance(values, tuple)

        for value in values:
            if name.endswith(" " + category) and value in name:
                name = name.rstrip(" " + category)

    return name


def unqualify(name):
    ''' remove qualifiers '''
    for qualifier in qualifiers:
        if name.startswith(qualifier):
            name = name[len(qualifier) + 1:]

    if name.endswith('egg'):
        name, _ = name.split(' egg')

    if name.endswith('eggs'):
        name, _ = name.split(' eggs')

    return name


def split(name):
    ''' add splits
    rockfish -> rock fish
    '''
    for s in splits:
        if (
            name != s
            and name.endswith(s)
            and not name.endswith(" " + s)
        ):
            name = name.replace(s, " " + s)
    return name


def unsplit(name):
    ''' remove splits
    rock fish -> rockfish
    '''
    for s in splits:
        if name != s and ' ' + s in name:
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

    def path(self):
        ''' where this is on the file system
        '''
        return os.path.join(utility.root, self.directory, self.label)

    def fullsize(self):
        ''' URI of full size image '''
        return "https://public.anardil.net/media/diving/{d}/{i}".format(
            d=self.directory, i=self.label,
        )

    def hash(self):
        ''' hash a file the same way indexer does, so we can find it's thumbnail
        '''
        sha1 = hashlib.sha1()

        with open(self.path(), "rb") as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha1.update(data)

        return sha1.hexdigest()

    def singular(self):
        ''' return singular version '''
        name = inflect.singular_noun(self.name.lower())
        name = name or self.name.lower()

        # fix inflect's mistakes
        for tofix in ("octopu", "gras", "fuscu"):
            if tofix in name and tofix + "s" not in name:
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
