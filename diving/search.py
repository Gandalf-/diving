#!/usr/bin/python3

import glob
import os
import re
import subprocess
from typing import Iterable, List

from diving.util.resource import VersionedResource
from diving.util.static import search_data_path


def write_search_data(
    gallery_pages: List[str], sites_pages: List[str], taxonomy_pages: List[str]
) -> None:
    """JSON site map for gallerySearch"""

    gallery_pages = list(_cleaner(gallery_pages))
    sites_pages = list(_cleaner(sites_pages))
    taxonomy_pages = list(_cleaner(taxonomy_pages))

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


def _cleaner(pages: List[str]) -> Iterable[str]:
    for page in pages:
        assert page.endswith('.html')
        page = os.path.basename(page)

        prefixes = ('index', 'various', 'adult', 'juvenile')
        if any(page.startswith(prefix) for prefix in prefixes):
            continue

        name = page.replace('.html', '').replace('-', ' ')
        name = DATE_PATTERN.sub(lambda m: m.group(0).replace(' ', '-'), name)
        yield f'"{name}"'
