"""Find species with missing or incomplete taxonomy data.

Two modes:

--missing: Lists image names with NO entry in taxonomy.yml
  Shows names that appear in image filenames but have no scientific name mapping.
  Excludes names in no-taxonomy-exact and no-taxonomy-any lists.

--incomplete: Lists image names where taxonomy lacks exact genus+species
  Shows names that have a taxonomy entry but the scientific name is imprecise:
  - Ends with 'sp.' (e.g., 'Polychaeta sp.' for 'worm')
  - Ends with a genus only (e.g., 'Leodice' for 'bobbit worm')
  - Has no species epithet

USAGE:
  $ python3 missing.py --missing     # show names without taxonomy
  $ python3 missing.py --incomplete  # show names without exact species
"""

import operator
from collections import Counter
from typing import Set

from diving.util import collection, static, taxonomy
from diving.util.image import split

NameMapping = dict[str, str]


def _lookup_scientific(name: str, mapping: NameMapping) -> str:
    """Lookup scientific name, reusing gallery_scientific for normalization.

    Pre-applies split() then lets gallery_scientific handle:
    - unsplit (angel fish -> angelfish)
    - uncategorize (seaweed algae -> seaweed)
    """
    return taxonomy.gallery_scientific([split(name)], mapping)


def count_missing_names() -> Counter[str]:
    """Names in images with no taxonomy.yml entry."""
    scientific = taxonomy.mapping()
    named_images = collection.expand_names(collection.named())

    missing: Counter[str] = Counter()

    for image in named_images:
        name = image.simplified()

        # Skip if in no-taxonomy lists
        if taxonomy.no_taxonomy([name]):
            continue

        # Skip if any word is in static.ignore (non-species like "reef", "site")
        if any(word in static.ignore for word in name.split()):
            continue

        # Check if name has a scientific mapping (try multiple normalizations)
        if not _lookup_scientific(name, scientific):
            missing[name] += 1

    return missing


def count_incomplete_names() -> Counter[str]:
    """Names in images with taxonomy but no exact genus+species."""
    scientific = taxonomy.mapping()
    named_images = collection.expand_names(collection.named())

    incomplete: Counter[str] = Counter()

    for image in named_images:
        name = image.simplified()

        # Must have a scientific mapping to be "incomplete" (vs "missing")
        sci_name = _lookup_scientific(name, scientific)
        if not sci_name:
            continue

        # Check if scientific name is incomplete
        if _is_incomplete(sci_name):
            incomplete[name] += 1

    return incomplete


def _is_incomplete(sci_name: str) -> bool:
    """Check if scientific name lacks a proper species epithet.

    A complete scientific name ends with a lowercase species epithet.
    Incomplete examples:
    - 'Animalia Chordata Actinopterygii sp.' (ends with sp.)
    - 'Animalia Annelida Polychaeta Leodice' (ends with genus, capitalized)
    """
    parts = sci_name.split()
    if not parts:
        return True

    last = parts[-1]

    # Explicit 'sp.' means unidentified species
    if last == 'sp.':
        return True

    # If last part is capitalized, it's a genus/family/etc, not a species
    # Species epithets are always lowercase
    if last[0].isupper():
        return True

    return False


def get_missing_names() -> Set[str]:
    return set(count_missing_names().keys())


def get_incomplete_names() -> Set[str]:
    return set(count_incomplete_names().keys())


def _print_counts(counts: Counter[str], label: str) -> None:
    """Print counts sorted by count, with total."""
    items = counts.items()
    total = 0
    for name, count in sorted(items, key=operator.itemgetter(1)):
        total += count
        print(name, count)
    print(f'total {label}', total)


def main_missing() -> None:
    """Print names without taxonomy entry."""
    _print_counts(count_missing_names(), 'missing')


def main_incomplete() -> None:
    """Print names without exact genus+species."""
    _print_counts(count_incomplete_names(), 'incomplete')
