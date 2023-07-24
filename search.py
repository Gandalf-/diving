#!/usr/bin/python3

import os

from typing import Iterable


def write_search_data() -> None:
    '''JSON site map for gallerySearch'''
    gal_pages = _reader('gallery')
    tax_pages = _reader('taxonomy')

    with open('search-data.js', 'w') as fd:
        fd.write('var gallery_pages = [')
        fd.write(','.join(gal_pages))
        fd.write('];\n')

        fd.write('var taxonomy_pages = [')
        fd.write(','.join(tax_pages))
        fd.write('];\n')


# PRIVATE


def _cleanup(name: str) -> str:
    name = name.replace('.html', '').replace('-', ' ')
    return f'"{name}"'


def _reader(path: str) -> Iterable[str]:
    for page in os.listdir(path):
        if not page.endswith('.html'):
            continue

        prefixes = ('index', 'various', 'juvenile')
        if any(page.startswith(prefix) for prefix in prefixes):
            continue

        yield _cleanup(page)
