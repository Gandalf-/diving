#!/usr/bin/env python3

'''
Attempt to translate Latin/Greek names to English based on roots, prefixes, and
suffixes
'''

from typing import List, NamedTuple, Dict, Set

from bs4 import BeautifulSoup

from util.common import source_root


class Entry(NamedTuple):
    latin: str
    lang: str
    english: str
    example: str
    roots: str


def is_lang(chunk: str) -> bool:
    if chunk == 'L[9]':
        return True

    chunk, *_ = chunk.replace(',', '').split(' ')
    return chunk in ('L', 'G')


def parse_table() -> List[Entry]:
    with open(source_root + 'data/names.html') as fd:
        content = fd.read()

    out = []

    soup = BeautifulSoup(content, 'html.parser')
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all('td'):
                row_data.append(cell.text.strip())

            if not row_data or row_data[0] == 'Latin/Greek':
                continue

            if len(row_data) == 4:
                row_data.append('')
            assert len(row_data) == 5, row_data

            roots = row_data[-1]
            for strip in ('beginning with', 'containing'):
                roots = roots.replace(f'All pages with titles {strip} ', '')

            ignore = ('No simple way to distinguish', 'Too common a letter combination')
            if any(i in roots for i in ignore):
                roots = ''

            row_data[-1] = roots.lower()

            row_data[0] = row_data[0].replace('-', '')
            row_data[0] = row_data[0].replace(' etc.', '')

            out.append(Entry(*row_data))

    return out


def get_roots(entry: Entry) -> Set[str]:
    names = ' '.join([entry.roots, entry.latin])
    names = names.replace(',', '').replace('-', '').replace('–', '')
    parts = [name.strip() for name in names.split(' ')]
    return set(p for p in parts if p)


def to_index(table: List[Entry]) -> Dict[str, str]:
    index = {
        'nudi': 'naked',
        'poda': 'footed',
        'sol': 'sun',
        'luna': 'moon',
        'aster': 'star',
        'oidea': 'shaped',
    }

    for entry in table:
        english, *_ = entry.english.split(', ')
        for root in get_roots(entry):
            index[root] = english

    return index


def translate(index: Dict[str, str], word: str) -> str:
    if word in index:
        return index[word]

    prefix = None
    prefixes = [word[:i] for i in range(len(word), 0, -1)]
    for p in prefixes:
        if p in index:
            prefix = index[p]
            print('found prefix', p, prefix, word, '->', word[len(p) :])
            word = word[len(p) :]
            break

    suffix = None
    suffixes = [word[i:] for i in range(len(word))]
    for s in suffixes:
        if s in index:
            suffix = index[s]
            word = word[: -len(s)]
            print('found suffix', s, suffix, word)
            break

    left = word if len(word) > 2 else None
    out = [o for o in [prefix, left, suffix] if o]

    return '-'.join(out)


def convert(word: str) -> str:
    pairs = {
        'nudi': 'naked',
        'branchia': 'gills',
        'gastro': 'stomach',
        'versicolor': 'many-colored',
        'giganteus': 'giant',
        'poda': 'footed',
        'pod': 'foot',
        'sol': 'sun',
        'hyper': 'over',
        'luna': 'moon',
        'aster': 'star',
        'oidea': 'shaped',
        'deca': 'ten',
        'cephalo': 'head',
        'panto': 'all',
    }

    for k, v in pairs.items():
        word = word.replace(k, f'-{v}-')

    return word.strip('-').replace('--', '-')
