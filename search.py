#!/usr/bin/python3

import os


def gallery_listing() -> None:
    '''JSON site map for gallerySearch'''
    pages = []

    for page in os.listdir('gallery'):
        if not page.endswith('.html'):
            continue

        prefixes = ('index', 'various', 'juvenile')
        if any(page.startswith(prefix) for prefix in prefixes):
            continue

        pages.append(page.replace('.html', '').replace('-', ' '))

    with open('gallery/search.js', 'w') as fd:
        fd.write('var gallery_pages = [')
        fd.write(','.join(f'"{page}"' for page in pages))
        fd.write('];')
