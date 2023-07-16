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

    words = english.split(' ')
    if len(words) == 2 and words[0] == 'Many':
        return '-'.join(words)

    return english


def translate(word: str) -> Optional[str]:
    '''
    Given a word, attempt to translate it to English based on the contents of
    data/translate.yml
    '''
    return _translations.get(word.lower())


def filter_translations() -> None:
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

    empty |= all_latin

    with open(yaml_path, 'w+') as fd:
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
    print(f'{percent_known:.2f}% ({known}/{known + unknown}) translations known')
