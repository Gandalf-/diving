'''
Generate thumbnails for images as needed, cache the sha1sum in the database
'''

from util.database import database


def hashed(image) -> str:
    '''Get the sha1sum for an original image, using the database as a cache'''
    return database.get('diving', 'cache', image.identifier(), 'hash')


def thumbnail(image) -> str:
    '''Get the name of the thumbnail for an original image'''
    sha1 = hashed(image)
    assert sha1
    return sha1 + '.jpg'
