#!/usr/bin/env python3

'''
Attempt to translate Latin/Greek names to English based on roots, prefixes, and
suffixes
'''

import os
import re
import yaml

from typing import Optional
from util.taxonomy import all_latin_words
from util.common import source_root

yaml_path = os.path.join(source_root, 'data/translate.yml')

with open(yaml_path) as fd:
    _translations = yaml.safe_load(fd)

PARENTHETICAL = re.compile(r' \(.*\)')


def cleanup(latin: str, english: Optional[str]) -> Optional[str]:
    if not english:
        return None

    # remove parenthesis groups
    english = PARENTHETICAL.sub('', english)

    if latin.lower() == english.lower():
        return None

    return english


def create_filtered_yaml() -> None:
    clean = {}
    empty = set()
    all_latin = all_latin_words()

    for latin, english in _translations.items():
        cleaned = cleanup(latin, english)
        if cleaned:
            clean[latin] = cleaned
        else:
            empty.add(latin)

        if latin in all_latin:
            all_latin.remove(latin)

    base, ext = os.path.splitext(yaml_path)

    with open(base + '-new' + ext, 'w+') as fd:
        fd.write('---\n')
        for latin, english in sorted(clean.items()):
            fd.write(f'{latin}: {english}\n')
        for latin in sorted(empty | all_latin):
            fd.write(f'{latin}:\n')


def lookup(word: str) -> Optional[str]:
    '''
    Given a word, attempt to translate it to English based on the contents of
    data/translate.yml
    '''
    return _translations.get(word)
