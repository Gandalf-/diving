#!/usr/bin/env python3

"""
Attempt to translate Latin/Greek names to English based on roots, prefixes, and
suffixes
"""

import os
import re
from typing import Dict, Optional

import yaml

from diving.util import static
from diving.util.metrics import metrics
from diving.util.taxonomy import all_latin_words

translations_yml = os.path.join(static.source_root, 'data/translations.yml')


with open(translations_yml) as fd:
    _translations = yaml.safe_load(fd)

# Execution


def translate(word: str) -> str:
    """
    Given a word, attempt to translate it to English based on the contents of
    data/translate.yml
    """
    out = _translations[word.lower()] or ''
    out = out.replace('-family', '').replace('-order', '')
    return out.encode('ascii', 'xmlcharrefreplace').decode('ascii')


# Updating translations


PARENTHETICAL = re.compile(r' \(.*\)')
AFTER_COMMA = re.compile(r',.*')


def cleanup(latin: str, english: Optional[str]) -> Optional[str]:
    if not english:
        return None

    # remove parenthesis and synonyms groups
    english = PARENTHETICAL.sub('', english)
    english = AFTER_COMMA.sub('', english)
    english = '-'.join(english.split(' '))

    words = english.split('-')
    if len(words) == 3 and english.startswith('Named-after-'):
        english = f"{words[2]}'s"

    return english


def filterer(translations: Dict[str, str]) -> None:
    clean = {}
    empty = set()
    all_latin = all_latin_words()

    for latin, english in translations.items():
        cleaned = cleanup(latin, english)
        if cleaned:
            clean[latin] = cleaned
        else:
            empty.add(latin)

        if latin in all_latin:
            all_latin.remove(latin)

    empty |= all_latin

    with open(translations_yml, 'w+') as fd:
        fd.write('---\n')

        for i, (latin, english) in enumerate(sorted(clean.items())):
            fd.write(f'{latin}: {english}\n')

        for i, latin in enumerate(sorted(empty)):
            if i % 40 == 0:
                fd.write('\n')
            fd.write(f'{latin}:\n')

    known = len(clean)
    unknown = len(empty)
    percent_known = known / (known + unknown) * 100
    print(f'\t{percent_known:.2f}% ({known}/{known + unknown}) translations known')


def main() -> None:
    filterer(_translations)
    metrics.summary('translator')
