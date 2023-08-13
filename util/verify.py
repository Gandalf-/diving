#!/usr/bin/python3

'''
Check for broken links, misspelled names, and more
'''

import difflib
import os
import re

from typing import List, Tuple, Iterable, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from util import common
from util import collection
from util import static
from util import taxonomy


def advisory_checks() -> None:
    '''informational'''
    try:
        required_checks()
    except AssertionError as e:
        print(e)


def required_checks() -> None:
    '''must pass'''
    _important_files_exist()
    _verify_yaml_keys()
    _link_check()
    _misspellings()
    _wrong_order()
    _no_duplicate_image_keys()
    _unusal_casing()


# PRIVATE


def _unusal_casing() -> None:
    '''Look for names that are not capitalized correctly.'''
    unusual = []
    ignore = {'BC'}

    for image in collection.named():
        for word in image.name.split(' '):
            if word.islower():
                continue
            if word == common.titlecase(word):
                continue
            if word in ignore:
                continue
            unusual.append(image.label)

    assert not unusual, f'Unusual casing found in {unusual}'


def _no_duplicate_image_keys() -> None:
    '''
    Ensure that no two files in the same dive directory have the same key.
    Images with the same name are fine, but the key must be different.
    '''
    dive_paths = collection.dive_listing()
    pattern = re.compile(r"(\d+)(.*)")

    for path in dive_paths:
        seen = set()

        for filename in os.listdir(path):
            match = pattern.match(filename)
            if not match:
                continue

            key = match.group(1)
            if key in seen:
                assert False, f'Duplicate key {key}, {filename} in {path}'
            seen.add(key)


def _verify_yaml_keys() -> None:
    '''
    Read the yaml file and check for duplicate keys. Duplicates shadow previous
    definitions making things appear to be missing when they are not.
    '''
    fname = taxonomy.yaml_path
    seen_keys = set()
    ignore = ('sp.', 'Pantopoda')
    duplicates = []

    invalid_keys = ('sp',)
    invalid = []

    with open(fname) as fd:
        for line in fd:
            if ':' not in line:
                continue

            key = line.split(':')[0].strip()
            if key in invalid_keys:
                invalid.append(key)

            if key in seen_keys and key not in ignore and key.istitle():
                duplicates.append(key)
            seen_keys.add(key)

    assert not duplicates, f'duplicate keys: {duplicates}'
    assert not invalid, f'invalid keys: {invalid}'


def _wrong_order() -> None:
    '''actual check'''
    tree = collection.build_image_tree()
    for value in _find_wrong_name_order(tree):
        assert False, f'word ordering appears wrong between {value}'


def _find_wrong_name_order(tree: Any) -> Iterable[Tuple[str, str]]:
    '''look for swapped words'''
    if not isinstance(tree, dict):
        return

    conflicts = []
    seen: Dict[str, str] = {}

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


def _misspellings() -> None:
    '''actual check'''
    found = set(_find_misspellings())
    if found:
        assert False, f'{found} may be mispelled'


def _find_misspellings(names: Optional[List[str]] = None) -> Iterable[str]:
    '''check for misspellings'''
    candidates = _possible_misspellings(names)
    scientific = taxonomy.mapping()
    ignores = (
        'clathria',
        'mauve spiky soft coral',
        'magenta spiky soft coral',
        'fan coral',
    )

    for group in candidates:
        for candidate in group:
            if taxonomy.gallery_scientific(candidate.split(' '), scientific):
                continue
            if any(i in candidate for i in ignores):
                continue

            yield candidate


def _possible_misspellings(
    names: Optional[List[str]] = None,
) -> Iterable[List[str]]:
    '''look for edit distance

    prune based on taxonomy.load_known()
    '''
    all_names = names or collection.all_names()

    while all_names:
        name = all_names.pop()
        if any(name.endswith(i) for i in static.ignore + ['unknown']):
            continue

        similars = difflib.get_close_matches(name, all_names, cutoff=0.8)
        similars = [
            other for other in similars if other not in name and name not in other
        ]
        if similars:
            yield [name] + similars


def _important_files_exist() -> None:
    '''basic sanity'''
    required = ['index.html', static.stylesheet.path, 'favicon.ico', 'imgs']
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


def _link_check() -> None:
    """check the html directory for broken links by extracting all the
    internal links from the written files and looking for those as paths
    """

    def check_link_exists(args: Tuple[str, str]) -> Optional[str]:
        path, link = args
        for attempt in (link, link + '.html', link + 'index.html'):
            if os.path.exists(attempt):
                return None
        return f'broken {link} in {path}'

    with ThreadPoolExecutor() as executor:
        broken = list(filter(None, executor.map(check_link_exists, _find_links())))

    assert not broken, broken


def _find_links() -> Iterable[Tuple[str, str]]:
    """check the html directory for internal links"""

    def extract_from(path: str) -> List[Tuple[str, str]]:
        """get links from a file"""
        links = []
        with open(path) as fd:
            content = fd.read()
            for link in re.findall(r'(?:href|src)=\"(.+?)\"', content):
                if link.startswith('http'):
                    continue

                link = link[1:]
                links.append((path, link))
        return links

    def process_file(directory: str, filename: str) -> List[Tuple[str, str]]:
        path = os.path.join(directory, filename)
        return extract_from(path)

    workers = (os.cpu_count() or 4) * 2
    with ThreadPoolExecutor(max_workers=workers) as executor:
        file_list = [
            (directory, filename)
            for directory in ('taxonomy', 'gallery', 'sites')
            for filename in os.listdir(directory)
            if filename.endswith(".html")
        ]
        links = executor.map(lambda args: process_file(*args), file_list)

    seen = set()
    for result in links:
        for path, link in result:
            if link not in seen:
                seen.add(link)
                yield (path, link)


if __name__ == '__main__':
    required_checks()
