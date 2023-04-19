#!/usr/bin/python3

'''
Check for broken links, misspelled names, and more
'''

import difflib
import os
import re

from typing import List, Tuple, Iterable, Dict, Any
from concurrent.futures import ThreadPoolExecutor

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


def _wrong_order() -> None:
    '''actual check'''
    tree = collection.build_image_tree()
    for value in _find_wrong_name_order(tree):
        assert False, f'word ordering appears wrong between {value}'


def _find_wrong_name_order(tree: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
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


def _misspellings() -> None:
    '''actual check'''
    found = set(_find_misspellings())
    if found:
        assert False, f'{found} may be mispelled'


def _find_misspellings(names: List[str] = None) -> Iterable[str]:
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


def _possible_misspellings(names: List[str] = None) -> Iterable[List[str]]:
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


def _important_files_exist() -> None:
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


def _link_check() -> None:
    """check the html directory for broken links by extracting all the
    internal links from the written files and looking for those as paths
    """

    def check_link_exists(args):
        path, link = args
        if not os.path.exists(link):
            return f'broken {link} in {path}'
        return None

    with ThreadPoolExecutor() as executor:
        broken = list(
            filter(None, executor.map(check_link_exists, _find_links()))
        )

    assert not broken, broken


def _find_links() -> Iterable[Tuple[str, str]]:
    """check the html directory for internal links"""

    def extract_from(path) -> List[Tuple[str, str]]:
        """get links from a file"""
        links = []
        with open(path, encoding='utf8') as fd:
            content = fd.read()
            for link in re.findall(r'(?:href|src)=\"(.+?)\"', content):
                if link.startswith('http'):
                    continue

                link = link[1:]
                links.append((path, link))
        return links

    def process_file(directory, filename) -> List[Tuple[str, str]]:
        path = os.path.join(directory, filename)
        return extract_from(path)

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
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
