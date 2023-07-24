#!/usr/bin/python3

import os


def write_search_data() -> None:
    '''JSON site map for gallerySearch'''
    gal_pages = []
    for page in os.listdir('gallery'):
        if not page.endswith('.html'):
            continue

        prefixes = ('index', 'various', 'juvenile')
        if any(page.startswith(prefix) for prefix in prefixes):
            continue

        gal_pages.append(_cleanup(page))

    tax_pages = []
    for page in os.listdir('taxonomy'):
        if not page.endswith('.html'):
            continue

        prefixes = ('index', 'various', 'juvenile')
        if any(page.startswith(prefix) for prefix in prefixes):
            continue

        tax_pages.append(_cleanup(page))

    with open('search-data.js', 'w') as fd:
        fd.write('var gallery_pages = [')
        fd.write(','.join(gal_pages))
        fd.write('];')

        fd.write('var taxonomy_pages = [')
        fd.write(','.join(tax_pages))
        fd.write('];')


def _cleanup(name: str) -> str:
    name = name.lower().replace('.html', '').replace('-', ' ')
    return f'"{name}"'
