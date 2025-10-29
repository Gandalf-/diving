#!/usr/bin/python3

"""Find and update images with imprecise names.

A name is imprecise if there exists another name that ends with but is not exactly equal to it.
For example, 'crab' is imprecise if you also have 'hermit crab' or 'spider crab'.

WORKFLOW:
1. List imprecise names and counts:
   $ python3 imprecise.py --list

2. Extract images for a specific imprecise name to temp directory:
   $ python3 imprecise.py --find 'crab'
   This creates hardlinks in ~/working/tmp/imprecise/crab/ with names like:
   - 000 Indonesia.jpg
   - 001 Philippines.jpg
   - 002 Caribbean.jpg

3. Manually rename files to specify new precise names:
   Add ' - <new_name>' before the extension:
   - 000 Indonesia.jpg  →  000 Indonesia - hermit crab.jpg
   - 001 Philippines.jpg  →  001 Philippines - spider crab.jpg
   (Leave files unchanged if they're already correct)
   (Capitalization doesn't matter)
   (Do not pluralize)

4. Apply the renames to original files:
   $ python3 imprecise.py --update 'crab'
   This will interactively prompt you to confirm each rename.
"""

import argparse
import operator
import os
from collections import Counter
from typing import List, Set

import locations
from util import collection, common, taxonomy
from util.image import Image, split


def total_imprecise() -> int:
    return sum(count_imprecise_names().values())


def count_imprecise_names() -> Counter[str]:
    all_names = collection.all_names()
    imprecise_names: Set[str] = set()

    # Find which names are imprecise (have longer variations)
    for name in all_names:
        if ' egg' in name:
            continue

        # Check if it appears as a suffix in other longer names
        for other in all_names:
            # Only check if the other name is longer and ends with this name preceded by a space
            if len(other) > len(name) and other.endswith(' ' + name):
                imprecise_names.add(name)
                break

    allowed = {
        'boat',
        'boat wreck',
        'building',
        'eggs',
        'rock',
        'seagull',
    }

    imprecise_names -= allowed

    # Count how many images have each imprecise name
    named_images = collection.expand_names(collection.named())
    imprecise: Counter[str] = Counter()

    for i in named_images:
        name = split(i.simplified())
        if name in imprecise_names:
            imprecise[name] += 1

    return imprecise


def get_imprecise_names() -> Set[str]:
    return set(count_imprecise_names().keys())


def get_imprecise_images() -> List[Image]:
    imprecise_names = get_imprecise_names()
    named_images = collection.expand_names(collection.named())
    imprecise_images = []

    for i in named_images:
        if split(i.simplified()) in imprecise_names:
            imprecise_images.append(i)

    return imprecise_images


def find_imprecise_images(name: str) -> List[Image]:
    """Find images with the given imprecise name.

    This matches against the split simplified name to avoid partial matches.
    For example, searching for "star" won't match "rockstar".
    """
    return [i for i in get_imprecise_images() if split(i.simplified()) == name]


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
    scientific = taxonomy.mapping()

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

        sci_name = scientific.get(new.lower(), '???')

        print(os.path.dirname(path))
        print('\t', os.path.basename(path))
        print('\t', f'{os.path.basename(tgt)} ({sci_name})')
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
