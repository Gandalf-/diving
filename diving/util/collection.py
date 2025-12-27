#!/usr/bin/python3

"""
parsing data from the file system to construct trees of images
"""

import os
from functools import lru_cache
from typing import Dict, Iterable, Iterator, List, Set, Union, cast

from diving.util import static
from diving.util.common import flatten, tree_size
from diving.util.image import Image, reorder_eggs, split
from diving.util.metrics import metrics

ImageTree = dict[str, Union[List[Image], 'ImageTree']]


def named() -> List[Image]:
    """all named images from all directories"""
    return flatten([[y for y in z if y.name] for z in _collect_all_images()])


def all_names() -> Set[str]:
    """all simplified, split names"""
    return {split(i.simplified()) for i in expand_names(named())}


@lru_cache(None)
def all_valid_names() -> Set[str]:
    return set(single_level(build_image_tree()).keys())


def single_level(tree: ImageTree) -> Dict[str, List[Image]]:
    """squash the tree into a single level name to images dict"""
    assert isinstance(tree, dict), tree

    def inner(where: ImageTree) -> Iterator[List[Image]]:
        for value in where.values():
            if isinstance(value, list):
                yield value
            else:
                yield from inner(value)

    out: Dict[str, List[Image]] = {}
    for group in inner(tree):
        name = group[0].simplified()

        out.setdefault(name, [])
        out[name] += group

    return out


@lru_cache(None)
def build_image_tree() -> ImageTree:
    """construct a nested dictionary where each key is a unique split of a
    name (after processing) from right to left. if there's another split under
    this one, the value is another dictionary, otherwise, it's a list of Images
    """
    return pipeline(_make_tree(expand_names(named())))


def pipeline(tree: ImageTree, reverse: bool = True) -> ImageTree:
    """intermediate steps!"""
    compressed = _compress(_compress(_compress(tree, reverse), reverse), reverse)
    pruned = _pruner(compressed)
    unnested = _unnest_complete_species(pruned)
    return _data_to_various(unnested)


@lru_cache(None)
def delve(dive_path: str) -> List[Image]:
    """
    Create an Image object for each labeled picture in a directory; the path
    provided must be absolute
    """
    directory = os.path.basename(dive_path)
    exts = ('.jpg', '.mov', '.mp4')
    entries = [
        entry
        for entry in os.listdir(dive_path)
        if any(entry.endswith(ext) for ext in exts) and '-' in entry
    ]
    return [Image(entry, directory, i / len(entries)) for i, entry in enumerate(sorted(entries))]


def expand_names(images: List[Image]) -> Iterator[Image]:
    """split out `a and b` into separate elements"""
    for image in images:
        for part in (' with ', ' and '):
            if part not in image.name:
                continue

            left, right = image.name.split(part)
            lnew = Image(image.label, image.directory)
            rnew = Image(image.label, image.directory)
            lnew.name = reorder_eggs(left)
            rnew.name = reorder_eggs(right)
            yield lnew
            yield rnew
            break
        else:
            yield image


@lru_cache(None)
def dive_listing() -> List[str]:
    """a list of all dive picture folders available"""
    return sorted(
        [
            os.path.join(static.image_root, dive)
            for dive in os.listdir(static.image_root)
            if dive.startswith('20')
        ]
    )


# PRIVATE


def _is_complete_species(name: str) -> bool:
    """Check if this name maps to a genus+species (not 'sp.') in taxonomy"""
    from diving.util import taxonomy

    mapping = taxonomy.mapping(taxonomy.MappingType.Gallery)
    scientific = mapping.get(name)

    if not scientific:
        return False

    parts = scientific.split()
    if len(parts) < 2:
        return False

    genus, species = parts[-2:]
    return genus[0].isupper() and species[0].islower() and species != 'sp.'


def _collect_all_images() -> List[List[Image]]:
    """run delve on all dive picture folders"""
    return [delve(dive_path) for dive_path in dive_listing()]


def _make_tree(images: Iterable[Image]) -> ImageTree:
    """make a nested dictionary by words"""
    out: ImageTree = {}

    for image in images:
        name = image.normalized()
        words = name.split(' ')[::-1]

        if words[0] in static.ignore:
            metrics.counter('images ignored while building image tree')
            continue

        sub = out
        for word in words:
            sub.setdefault(word, {})
            sub = cast(ImageTree, sub[word])

        sub.setdefault('data', [])
        cast(List[Image], sub['data']).append(image)

    return out


def _pruner(tree: ImageTree, too_few: int = 5) -> ImageTree:
    """remove top level keys with too few elements"""
    to_remove = []
    allow = {'reef squid'}

    for key, value in tree.items():
        if tree_size(value) <= too_few:
            to_remove.append(key)

    for remove in to_remove:
        if remove in allow:
            continue
        metrics.record('images pruned by count', remove)
        tree.pop(remove)

    return tree


def _compress(tree: ImageTree, reverse: bool = True) -> ImageTree:
    """look for sub trees with no 'data' key, which can be squished up a level"""
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if not isinstance(value, dict):
            continue

        if 'data' not in value and len(value.keys()) == 1:
            v = cast(ImageTree, tree.pop(key))
            s = list(v.keys())[0]

            if reverse:
                new_key = f'{s} {key}'
            else:
                new_key = f'{key} {s}'

            child = cast(ImageTree, v[s])
            tree[new_key] = _compress(child, reverse)
        else:
            tree[key] = _compress(value, reverse)

    return tree


def _find_promotable_children(
    parent_key: str, parent_value_dict: ImageTree, parent_simplified: str
) -> List[tuple[str, str, ImageTree]]:
    """Find children that should be promoted to siblings because they are complete species."""
    promotable = []

    for child_key, child_value in list(parent_value_dict.items()):
        if child_key == 'data' or not isinstance(child_value, dict):
            continue

        child_value_dict = cast(ImageTree, child_value)
        if 'data' not in child_value_dict:
            continue

        child_images = cast(List[Image], child_value_dict['data'])
        if not child_images:
            continue

        child_simplified = child_images[0].simplified()

        # Check if child is also a complete species AND different from parent
        if _is_complete_species(child_simplified) and child_simplified != parent_simplified:
            new_key = f'{child_key} {parent_key}'
            promotable.append((child_key, new_key, child_value))
            metrics.counter('images un-nested complete species')

    return promotable


def _unnest_complete_species(tree: ImageTree) -> ImageTree:
    """
    Post-process tree to unnest complete species that were incorrectly nested.

    When a node has both 'data' and child nodes, check if the images in 'data'
    represent a complete species. If so, and any child nodes would also form
    complete species when combined with the parent key, promote those children
    to be siblings instead.

    Example:
        Before: {coral: {staghorn: {data: [...], fused: {data: [...]}}}}
        After:  {coral: {staghorn: {data: [...]}, 'fused staghorn': {data: [...]}}}
    """
    assert isinstance(tree, dict), tree

    for parent_key, parent_value in list(tree.items()):
        if parent_key == 'data' or not isinstance(parent_value, dict):
            continue

        # Recursively process children first
        tree[parent_key] = _unnest_complete_species(parent_value)
        parent_value = tree[parent_key]

        if 'data' not in parent_value:
            continue

        parent_value_dict = cast(ImageTree, parent_value)
        images = cast(List[Image], parent_value_dict['data'])
        if not images:
            continue

        parent_simplified = images[0].simplified()
        if not _is_complete_species(parent_simplified):
            continue

        # Find and promote children that are complete species
        for old_key, new_key, child_value in _find_promotable_children(
            parent_key, parent_value_dict, parent_simplified
        ):
            del parent_value_dict[old_key]
            tree[new_key] = child_value

    return tree


def _data_to_various(tree: ImageTree) -> ImageTree:
    """rebucket data into various"""
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if key == 'data':
            if len(tree.keys()) == 1:
                # we're alone, don't nest further
                continue

            values = tree.pop('data')
            assert 'various' not in tree
            tree['various'] = {'data': values}

        else:
            tree[key] = _data_to_various(cast(ImageTree, value))

    children = set(tree.keys())
    if 'various' in children:
        children -= {'various', 'gravid', 'juvenile', 'eggs', 'mating'}
        if not children:
            metrics.counter('image groups detected as adults')
            adults = tree.pop('various')
            tree['adult'] = adults

    return tree
