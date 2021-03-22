#!/usr/bin/python3

'''
identification game
'''

import shutil
import os
import subprocess
import yaml

from apocrypha.client import Client

from image import unqualify, categorize, split
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
    client = Client('elm.anardil.net')
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


def filter_images(images, debug=True):
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
            if debug:
                print(simple, 'has qualifiers')
            continue

        if simple not in knowns:
            if debug:
                print(simple, 'no taxonomy')
            continue

        all_names.append(simple)
        new_images.append(image)

    return all_names, new_images


def difficulties(names):
    ''' get difficulty overrides
    '''
    with open('data/static.yml') as fd:
        data = yaml.safe_load(fd)['difficulty']

    lookup = {
        'very easy': 0,
        'easy': 0,
        'moderate': 2,
        'hard': 3,
        'very hard': 4,
    }

    mapping = {}
    for key, values in data.items():
        for value in values:
            mapping[value] = lookup[key]

    out = []
    for name in names:
        name = name.lower()
        name = split(categorize(name)).split(' ')[-1]
        out.append(mapping.get(name, 0))
    return out


def table_builder(debug=True):
    ''' build the tables!
    '''
    # reversing so we get newer things first
    images = reversed(list(collection.named()))
    all_names, images = filter_images(images, debug)

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
    diffs = difficulties(names)

    return names, thumbs, similarity, diffs


def inspect_choices():
    ''' build a directory tree of chosen thumbnails for visual inspection
    '''
    ns, ts, _, _ = table_builder(False)
    root = '/mnt/zfs/working'
    source = os.path.join(root, 'object-publish/diving-web/imgs')
    output = os.path.join(root, 'tmp/detective')
    root = 3489204839483

    if os.path.exists(output):
        shutil.rmtree(output)
    os.mkdir(output)

    for i, name in enumerate(ns):
        os.mkdir(os.path.join(output, name))

        for j, thumb in enumerate(ts[i]):
            src = os.path.join(source, thumb + '.jpg')
            dst = os.path.join(output, name, f'{j:02} ' + thumb + '.jpg')
            os.link(src, dst)


def javascript(debug=True):
    ''' write out the tables to a file
    '''
    ns, ts, ss, ds = table_builder(debug)

    with open('detective/data.js', 'w+') as fd:
        print('var names =', ns, file=fd)
        print('var thumbs =', ts, file=fd)
        print('var similarities =', ss, file=fd)
        print('var difficulties =', ds, file=fd)
