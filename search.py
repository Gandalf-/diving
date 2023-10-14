#!/usr/bin/python3

import glob
import os
import re
import subprocess
from typing import Iterable

from util.static import VersionedResource, search_data_path


def write_search_data() -> None:
    '''JSON site map for gallerySearch'''
    gallery_pages = _reader('gallery')
    taxonomy_pages = _reader('taxonomy')
    sites_pages = _reader('sites')

    with open(search_data_path, 'w') as fd:
        fd.write('var gallery_pages = [')
        fd.write(','.join(gallery_pages))
        fd.write('];\n')

        fd.write('var taxonomy_pages = [')
        fd.write(','.join(taxonomy_pages))
        fd.write('];\n')

        fd.write('var sites_pages = [')
        fd.write(','.join(sites_pages))
        fd.write('];\n')

    vr = VersionedResource(search_data_path)
    vr.cleanup()
    vr.write()

    indices = glob.glob('*/index.html')
    subprocess.run(['sed', '-i', '', f's/{search_data_path}/{vr.path}/', *indices])


# PRIVATE

DATE_PATTERN = re.compile(r'\d{4} \d{2} \d{2}')


def _cleanup(name: str) -> str:
    name = name.replace('.html', '').replace('-', ' ')
    name = DATE_PATTERN.sub(lambda m: m.group(0).replace(' ', '-'), name)
    return f'"{name}"'


def _reader(path: str) -> Iterable[str]:
    for page in os.listdir(path):
        if not page.endswith('.html'):
            continue

        prefixes = ('index', 'various', 'juvenile')
        if any(page.startswith(prefix) for prefix in prefixes):
            continue

        yield _cleanup(page)
