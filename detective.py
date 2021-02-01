#!/usr/bin/python3

'''
identification game
'''

import subprocess

from apocrypha.client import Client

from image import unqualify
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
        label = image.identifier()
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


def filter_images(images):
    ''' strip out images that are poor fits for the game
    - multiple subjects
    - vague, like "sponge"
    - no taxonomy, suggesting things like "dive site"
    '''
    knowns = set(taxonomy.load_known(exact_only=True))
    all_names = []
    new_images = []

    for image in images:

        # skip old pictures until cleaned up
        if image.directory.startswith('2019-09'):
            continue
        if image.directory.startswith('2017'):
            continue

        # skip bonaire until cleaned up
        if 'Bonaire' in image.directory:
            continue

        # take the first subject when there are multiple
        for part in (" with ", " and "):
            if part in image.name:
                left, _ = image.name.split(part)
                image.name = left

        # no qualified subjects: fish eggs, juvenile rock fish
        simple = image.singular().lower()
        if unqualify(simple) != simple:
            print(simple, 'has qualifiers')
            continue

        if simple not in knowns:
            print(simple, 'no taxonomy')
            continue

        all_names.append(simple)
        new_images.append(image)

    return all_names, new_images


def table_builder():
    ''' build the tables!
    '''
    # reversing so we get newer things first
    images = reversed(list(collection.named()))
    all_names, images = filter_images(images)

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
