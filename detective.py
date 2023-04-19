#!/usr/bin/python3

'''
identification game
'''

import shutil
import os
import pathlib

from typing import List, Optional, Iterable, Tuple

from util import collection
from util import static
from util import taxonomy

from util.common import titlecase
from util.image import unqualify, categorize, split, Image


root = str(pathlib.Path(__file__).parent.absolute()) + '/'


def get_hashes(images: List[Image]) -> Iterable[str]:
    '''cache in a database'''
    for image in images:
        sha1 = image.hashed()
        assert sha1, f'{image.path()} has no hash'
        yield sha1


ThumbsTable = List[List[str]]
SimiliarityTable = List[List[int]]
DifficultyTable = List[int]


def table_builder(
    debug: bool = True,
) -> Tuple[List[str], ThumbsTable, SimiliarityTable, DifficultyTable]:
    '''Build the tables.'''
    images = reversed(list(collection.named()))
    all_names, images = _filter_images(images, debug)

    hashes = list(get_hashes(images))
    names = sorted(list(set(all_names)))
    thumbs: ThumbsTable = [[] for _ in names]

    for i, name in enumerate(all_names):
        where = names.index(name)
        if len(thumbs[where]) <= 25:
            thumbs[where].append(hashes[i])

    similarity = _similarity_table(names)
    names = [titlecase(n) for n in names]
    diffs = _difficulties(names)

    return names, thumbs, similarity, diffs


def javascript(debug: bool = True) -> None:
    '''write out the tables to a file'''
    ns, ts, ss, ds = table_builder(debug)

    # This saves 100KB of data, ~20% of the total
    ts = str(ts).replace(' ', '')
    ss = str(ss).replace(' ', '')
    ds = str(ds).replace(' ', '')

    with open('detective/data.js', 'w+', encoding='utf8') as fd:
        print('var names =', ns, file=fd)
        print('var thumbs =', ts, file=fd)
        print('var similarities =', ss, file=fd)
        print('var difficulties =', ds, file=fd)


# PRIVATE


def _distance(
    a: str, b: str, tree: Optional[taxonomy.TaxiaTree] = None
) -> float:
    '''similarity score, higher means more different

    difflib.SequenceMatcher and jellyfish were all junk
    '''
    if not tree:
        tree = taxonomy.mapping()

    at = tree[a].split(' ')
    bt = tree[b].split(' ')

    total = 0
    match = 0

    for (x, y) in zip(at, bt):
        total += 1
        if x == y:
            match += 1

    return match / total


def _difficulties(names: List[str]) -> DifficultyTable:
    '''get difficulty overrides'''
    lookup = {
        'very easy': 0,
        'easy': 0,
        'moderate': 2,
        'hard': 3,
        'very hard': 4,
    }

    mapping = {}
    for key, values in static.difficulty.items():
        for value in values:
            mapping[value] = lookup[key]

    out = []
    for name in names:
        name = name.lower()
        name = split(categorize(name)).split(' ')[-1]
        out.append(mapping.get(name, 0))
    return out


def _filter_images(
    images: Iterable[Image], debug: bool = True
) -> Tuple[List[str], List[Image]]:
    '''strip out images that are poor fits for the game
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


def _similarity_table(names: List[str]) -> SimiliarityTable:
    '''how alike is every name pair'''
    tree = taxonomy.mapping()
    similarity: SimiliarityTable = [[] for _ in names]

    for i, name in enumerate(names):
        for j, other in enumerate(names):

            if i == j:
                similarity[i].append(0)
                continue

            if j > i:
                # should already be done
                continue

            d = _distance(name, other, tree)
            d = int(d * 100)
            similarity[i].append(d)

    return similarity


# INFORMATIONAL


def _inspect_choices() -> None:
    '''build a directory tree of chosen thumbnails for visual inspection'''
    ns, ts, _, _ = table_builder(False)

    oroot = '/mnt/zfs/working'
    source = os.path.join(oroot, 'object-publish/diving-web/imgs')
    output = os.path.join(oroot, 'tmp/detective')

    if os.path.exists(output):
        shutil.rmtree(output)
    os.mkdir(output)

    for i, name in enumerate(ns):
        os.mkdir(os.path.join(output, name))

        for j, thumb in enumerate(ts[i]):
            src = os.path.join(source, thumb + '.jpg')
            dst = os.path.join(output, name, f'{j:02} ' + thumb + '.jpg')
            os.link(src, dst)
