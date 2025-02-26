#!/usr/bin/python3

""" 
For each name, the name is imprecise if there exists another name that ends with but is not
exactly equal to the name. 
"""

import argparse
import operator
import os
from collections import Counter
from typing import List, Set

import locations
from util import collection, common
from util.image import Image


def total_imprecise() -> int:
    return sum(count_imprecise_names().values())


def count_imprecise_names() -> Counter[str]:
    all_names = collection.all_names()
    imprecise: Counter[str] = Counter()

    # For each name (potentially imprecise)
    for name in all_names:
        # Check if it appears as a suffix in other longer names
        for other in all_names:
            # Only check if the other name is longer and ends with this name preceded by a space
            if len(other) > len(name) and other.endswith(' ' + name):
                imprecise[name] += 1

    allowed = {
        'boat',
        'boat wreck',
        'building',
        'eggs',
        'rock',
        'seagull',
    }

    for a in allowed:
        imprecise.pop(a, None)

    return imprecise


def get_imprecise_names() -> Set[str]:
    return set(count_imprecise_names().keys())


def get_imprecise_images() -> List[Image]:
    imprecise_names = get_imprecise_names()
    named_images = collection.expand_names(collection.named())
    imprecise_images = []

    for i in named_images:
        if i.simplified() in imprecise_names:
            imprecise_images.append(i)

    return imprecise_images


def find_imprecise_images(name: str) -> List[Image]:
    """Find images with the given imprecise name.

    This matches against the full simplified name to avoid partial matches.
    For example, searching for "star" won't match "rockstar".
    """
    return [i for i in get_imprecise_images() if i.simplified() == name]


def save_imprecise(name: str) -> None:
    images = find_imprecise_images(name)

    root = os.path.expanduser(f'~/working/tmp/imprecise/{name}')
    if os.access(root, os.F_OK):
        # remove existing images
        for i in os.listdir(root):
            os.remove(os.path.join(root, i))
    else:
        os.mkdir(root)

    for n, image in enumerate(images):
        src = image.path()
        where = locations.get_region(image.site())

        _, extension = os.path.splitext(image.label)
        tgt = os.path.join(root, f'{n:03d} {where}{extension}')
        print(src)
        os.link(src, tgt)


def find_updates(name: str) -> List[str]:
    root = os.path.expanduser(f'~/working/tmp/imprecise/{name}')
    imprecise_paths = [os.path.join(root, p) for p in os.listdir(root)]

    renamed_paths = []
    for path in imprecise_paths:
        label = os.path.basename(path)
        if '-' not in label:
            continue
        renamed_paths.append(path)

    return renamed_paths


def update_imprecise(name: str) -> None:
    updates = find_updates(name)
    if not updates:
        return

    images = find_imprecise_images(name)
    inode_to_image = {}

    for image in images:
        inode = os.stat(image.path()).st_ino
        inode_to_image[inode] = image

    for update in updates:
        inode = os.stat(update).st_ino
        image = inode_to_image[inode]

        new = os.path.basename(update)
        _, new = new.split(' - ')
        new, _ = new.split('.')
        new = common.titlecase(new)
        old = common.titlecase(name)

        path = image.path()
        tgt = path.replace(old, new)

        print(os.path.dirname(path))
        print('\t', os.path.basename(path))
        print('\t', os.path.basename(tgt))
        print('? ', end='')
        keep = input()
        if keep and 'n' in keep:
            print('skipping')
            print('')
            continue

        os.rename(path, tgt)
        os.unlink(update)
        print('')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-l', '--list', action='store_true', help='list imprecise names')
    parser.add_argument('-f', '--find', help='find imprecise images by name')
    parser.add_argument('-u', '--update', help='update imprecise images by name')
    args = parser.parse_args()

    if args.list:
        items = count_imprecise_names().items()
        total = 0
        for name, count in sorted(items, key=operator.itemgetter(1)):
            total += count
            print(name, count)
        print('total', total)

    elif args.find:
        save_imprecise(args.find)

    elif args.update:
        update_imprecise(args.update)


if __name__ == '__main__':
    main()
