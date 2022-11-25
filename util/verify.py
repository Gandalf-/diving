#!/usr/bin/python3

'''
Check for broken links, misspelled names, and more
'''

import difflib
import os
import re

from util import collection
from util import static
from util import taxonomy


def advisory_checks():
    '''informational'''
    try:
        required_checks()
    except AssertionError as e:
        print(e)


def required_checks():
    '''must pass'''
    _important_files_exist()
    _link_check()
    _misspellings()
    _wrong_order()


# PRIVATE


def _wrong_order():
    '''actual check'''
    tree = collection.go()
    for value in _find_wrong_name_order(tree):
        assert False, f'word ordering appears wrong between {value}'


def _find_wrong_name_order(tree):
    '''look for swapped words'''
    if not isinstance(tree, dict):
        return

    conflicts = []
    seen = {}

    for key in tree.keys():
        flattened = ' '.join(sorted(key.split(' ')))

        if flattened in seen:
            conflicts.append(
                (
                    seen[flattened],
                    key,
                )
            )
        else:
            seen[flattened] = key

    yield from conflicts
    for value in tree.values():
        yield from _find_wrong_name_order(value)


def _misspellings():
    '''actual check'''
    found = list(_find_misspellings())
    assert not found, found


def _find_misspellings(names=None):
    '''check for misspellings'''
    candidates = _possible_misspellings(names)
    scientific = taxonomy.mapping()
    ignores = (
        'clathria',
        'mauve spiky soft coral',
        'fan coral',
    )

    for group in candidates:
        for candidate in group:
            if taxonomy.gallery_scientific(candidate.split(' '), scientific):
                continue
            if any(i in candidate for i in ignores):
                continue

            yield candidate


def _possible_misspellings(names=None):
    '''look for edit distance

    prune based on taxonomy.load_known()
    '''
    if not names:
        names = collection.all_names()

    while names:
        name = names.pop()
        if any(name.endswith(i) for i in static.ignore + ['unknown']):
            continue

        similars = difflib.get_close_matches(name, names, cutoff=0.8)
        similars = [
            other
            for other in similars
            if other not in name and name not in other
        ]
        if similars:
            yield [name] + similars


def _important_files_exist():
    '''basic sanity'''
    required = ['index.html', 'style.css', 'favicon.ico', 'imgs']
    required += [
        'jquery.fancybox.min.css',
        'jquery.fancybox.min.js',
    ]
    required += [
        f'{site}/index.html'
        for site in ['sites', 'detective', 'taxonomy', 'timeline', 'gallery']
    ]
    required += [
        'gallery/nudibranch.html',
        'gallery/giant-pacific-octopus.html',
        'taxonomy/Animalia.html',
        'taxonomy/Animalia-Mollusca-Gastropoda-Nudibranchia.html',
        'sites/Bonaire.html',
        'sites/Washington-Sund-Rock.html',
        'detective/data.js',
        'detective/game.js',
        'timeline/2021-12-16-Fort-Worden.html',
        'timeline/2020-09-04-Metridium.html',
    ]
    for fpath in required:
        assert os.path.exists(fpath), f'required file {fpath} does not exist'


def _link_check():
    """check the html directory for broken links by extracting all the
    internal links from the written files and looking for those as paths
    """
    for path, link in _find_links():
        assert os.path.exists(link), f'broken {link} in {path}'


def _find_links():
    """check the html directory for internal links"""

    def extract_from(fd):
        """get links from a file"""
        for line in fd:
            if 'href' not in line:
                continue

            for link in re.findall(r'href=\"(.+?)\"', line):
                if link.startswith('http'):
                    continue

                link = link[1:]
                yield path, link

    for directory in ('taxonomy', 'gallery', 'sites'):
        for filename in os.listdir(directory):
            if not filename.endswith(".html"):
                continue

            path = os.path.join(directory, filename)
            with open(path, encoding='utf8') as fd:
                yield from extract_from(fd)


if __name__ == '__main__':
    required_checks()
