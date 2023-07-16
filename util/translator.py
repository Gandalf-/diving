#!/usr/bin/env python3

'''
Attempt to translate Latin/Greek names to English based on roots, prefixes, and
suffixes
'''

import copy
import os
import re
import yaml

from typing import Optional, Dict
from util.taxonomy import all_latin_words
from util.common import source_root

v3_path = os.path.join(source_root, 'data/translate-3.yml')
v4_path = os.path.join(source_root, 'data/translate-4.yml')


with open(v3_path) as fd:
    _v3 = yaml.safe_load(fd)
    _translations = copy.deepcopy(_v3)

with open(v4_path) as fd:
    _v4 = yaml.safe_load(fd)

    for key, value in _v4.items():
        if not value:
            continue
        _translations[key] = value


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

    return english


def translate(word: str) -> Optional[str]:
    '''
    Given a word, attempt to translate it to English based on the contents of
    data/translate.yml
    '''
    return _translations.get(word.lower())


def filterer(translations: Dict[str, str], path: str, desc: str) -> None:
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

    with open(path, 'w+') as fd:
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
    print(
        f'\t{percent_known:.2f}% ({known}/{known + unknown}) {desc} translations known'
    )


def filter_translations() -> None:
    filterer(_v3, v3_path, 'fast')
    filterer(_v4, v4_path, 'quality')
