'''
Generate thumbnails for images as needed, cache the sha1sum in the database
'''

import subprocess
import os
from apocrypha.client import Client

from util import collection
from util import common


_database = Client()


def hashed(image) -> str:
    '''Get the sha1sum for an original image, using the database as a cache'''
    return _database.get('diving', 'cache', image.identifier(), 'hash')


def thumbnail(image) -> str:
    '''Get the name of the thumbnail for an original image'''
    sha1 = hashed(image)
    assert sha1
    return sha1 + '.jpg'


def generate_all() -> None:
    '''Generate thumbnails for all images'''
    hash_needed = []

    for image in scanner():
        data = _database.get('diving', 'cache', image.identifier())
        if not data:
            hash_needed.append(image)

        mtime = int(os.stat(common.root, image.directory, image.label))
        if data['mtime'] != mtime:
            hash_needed.append(image)

    bulk_hasher(hash_needed)


# PRIVATE


def scanner():
    '''Produce a stream of image paths'''
    for dive in os.listdir(common.root):
        yield from collection.delve(dive)


def bulk_hasher(images, batch: int = 50) -> None:
    '''Using an external process is faster'''
    while images:
        print('.', end='', flush=True)

        batch = images[:batch]
        paths = [i.path() for i in batch]

        out = subprocess.check_output(['sha1sum'] + paths).decode().strip('\n')

        for i, line in enumerate(out.split('\n')):
            sha1, *_ = line.split(' ')
            _database.set(
                'diving', 'cache', batch[i].identifier(), 'hash', value=sha1
            )

        images = images[batch:]
