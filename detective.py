#!/usr/bin/python3

'''
identification game
'''

import subprocess

from apocrypha.client import Client

import collection
import taxonomy


def distance(a, b, tree=None):
    ''' similarity score, higher means more different

    difflib.SequenceMatcher and jellyfish were all junk
    '''
    if not tree:
        tree = taxonomy.invert_known(taxonomy.load_tree())

    at = tree[a].split(' ')
    bt = tree[b].split(' ')

    total = 0
    match = 0

    for (x, y) in zip(at, bt):
        total += 1
        if x == y:
            match += 1

    return match / total


def cache_hash(images):
    ''' cache in a database
    '''
    client = Client()
    needed = []
    labels = []

    for image in images:
        label = image.directory + ':' + image.number
        sha1 = client.get('diving', 'cache-hash', label)

        if not sha1:
            needed.append(image)
            labels.append(label)
            continue

        if needed:
            bulk = hasher(needed)
            for (l, h) in zip(labels, bulk):
                client.set('diving', 'cache-hash', l, value=h)

            needed = []
            labels = []
            yield from bulk

        yield sha1

    bulk = hasher(needed)
    for (l, h) in zip(labels, bulk):
        client.set('diving', 'cache-hash', l, value=h)

    yield from bulk


def hasher(images, size=250):
    ''' [Image] -> [file hash]
    so we can hash in bulk
    '''
    while images:
        print('.', end='', flush=True)

        batch = images[:size]
        paths = [i.path() for i in batch]

        out = subprocess.check_output(['sha1sum'] + paths).decode()
        for line in out.split('\n'):
            if not line:
                continue
            sha1, *_ = line.split(' ')
            yield sha1

        images = images[size:]


def similarity_table(names):
    ''' how alike is every name pair
    '''
    tree = taxonomy.invert_known(taxonomy.load_tree())
    similarity = [[] for _ in names]

    for i, name in enumerate(names):
        for j, other in enumerate(names):

            if i == j:
                similarity[i].append(0)
                continue

            if j > i:
                # should already be done
                continue

            d = distance(name, other, tree)
            d = int(d * 100)
            similarity[i].append(d)

    return similarity


def table_builder():
    ''' build the tables!
    '''
    # reversing so we get newer things first
    images = reversed(list(collection.expand_names(collection.named())))
    knowns = set(taxonomy.load_known())

    all_names = []
    new_images = []

    for image in images:
        simple = image.simplified()
        if simple not in knowns:
            continue
        all_names.append(simple)
        new_images.append(image)

    images = new_images
    hashes = list(cache_hash(images))

    # names array
    names = sorted(list(set(all_names)))

    # thumbnail table
    thumbs = [[] for _ in names]
    for i, name in enumerate(all_names):
        where = names.index(name)

        if len(thumbs[where]) > 25:
            continue

        thumbs[where].append(hashes[i])

    similarity = similarity_table(names)
    names = [n.title() for n in names]

    return names, thumbs, similarity


def javascript():
    ''' write out the tables to a file
    '''
    ns, ts, ss = table_builder()

    with open('detective/data.js', 'w+') as fd:
        print('var names =', ns, file=fd)
        print('var thumbs =', ts, file=fd)
        print('var similarities =', ss, file=fd)
