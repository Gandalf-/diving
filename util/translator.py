#!/usr/bin/env python3

'''
Attempt to translate Latin/Greek names to English based on roots, prefixes, and
suffixes
'''

import os
import re
import yaml

from typing import Optional, Dict
from util.taxonomy import all_latin_words
from util.common import source_root

v4_path = os.path.join(source_root, 'data/translate-4.yml')


with open(v4_path) as fd:
    _translations = yaml.safe_load(fd)

# Execution


def translate(word: str) -> str:
    '''
    Given a word, attempt to translate it to English based on the contents of
    data/translate.yml
    '''
    out = _translations[word.lower()] or ''
    return out.replace('-family', '').replace('-order', '')


# Updating translations


PARENTHETICAL = re.compile(r' \(.*\)')
AFTER_COMMA = re.compile(r',.*')


def cleanup(latin: str, english: Optional[str]) -> Optional[str]:
    if not english:
        return None

    # remove parenthesis and synonyms groups
    english = PARENTHETICAL.sub('', english)
    english = AFTER_COMMA.sub('', english)

    if latin.lower() == english.lower():
        return None

    english = '-'.join(english.split(' '))

    words = english.split('-')
    if len(words) == 3 and english.startswith('Named-after-'):
        english = f'{words[2]}\'s'

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

    with open(v4_path, 'w+') as fd:
        fd.write('---\n')

        for i, (latin, english) in enumerate(sorted(clean.items())):
            if i % 40 == 0:
                fd.write('\n')
            fd.write(f'{latin}: {english}\n')

        for i, latin in enumerate(sorted(empty)):
            if i % 40 == 0:
                fd.write('\n')
            fd.write(f'{latin}:\n')

    known = len(clean)
    unknown = len(empty)
    percent_known = known / (known + unknown) * 100
    print(f'\t{percent_known:.2f}% ({known}/{known + unknown}) translations known')


def filter_translations() -> None:
    filterer(_translations)
