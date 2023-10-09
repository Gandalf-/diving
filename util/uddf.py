#!/usr/bin/python3

'''
Parsing UDDF files

https://www.streit.cc/extern/uddf_v321/en/index.html
'''

import os
import math
from functools import lru_cache
from typing import Dict, Any, Iterator, List
from datetime import datetime

import lxml

from util import collection

DiveInfo = Dict[str, Any]

root = '/Users/leaf/Desktop/Perdix/'


class Dive:
    def __init__(self, desc: DiveInfo) -> None:
        self.desc = desc


def meters_to_feet(m: float) -> int:
    return int(m * 3.28084)


@lru_cache(None)
def parse(file: str) -> DiveInfo:
    tree = lxml.etree.parse(os.path.join(root, file))  # type: ignore

    date = datetime.fromisoformat(
        tree.xpath(
            '//uddf:informationbeforedive/uddf:datetime/text()', namespaces=NAMESPACES
        )[0]
    )

    number = _parse_number(tree, '//uddf:informationbeforedive/uddf:divenumber')
    depth = _parse_number(tree, '//uddf:informationafterdive/uddf:greatestdepth')
    duration = _parse_number(tree, '//uddf:informationafterdive/uddf:diveduration')

    tank_start = _parse_number(
        tree, '//uddf:dive/uddf:tankdata/uddf:tankpressurebegin[position()=1]'
    )
    tank_end = _parse_number(
        tree, '//uddf:dive/uddf:tankdata/uddf:tankpressureend[position()=1]'
    )

    if math.isnan(tank_start) or math.isnan(tank_end):
        tank_start = 0
        tank_end = 0

    return {
        'date': date,
        'number': int(number),
        'depth': meters_to_feet(depth),
        'duration': int(duration),
        'tank_start': int(tank_start),
        'tank_end': int(tank_end),
    }


def load_dive_info() -> Iterator[DiveInfo]:
    for candidate in os.listdir(root):
        if not candidate.endswith('.uddf'):
            continue

        info = parse(candidate)
        if info['duration'] <= 900:
            continue
        if info['depth'] <= 10:
            continue

        yield info


def build_dive_history() -> Dict[str, List[str]]:
    '''No caching possible here since the consumer modifies the result to
    track progress through multi-dive days. Plus, dive_listing is already cached
    '''
    history: Dict[str, List[str]] = {}
    for dive in [os.path.basename(dive) for dive in collection.dive_listing()]:
        date, name = dive.split(' ', 1)
        history.setdefault(date, [])
        history[date].append(name)
    return history


def match_dive_info(infos: Iterator[DiveInfo]) -> Iterator[DiveInfo]:
    history = build_dive_history()

    for info in sorted(infos, key=lambda i: i['number']):
        date = info['date'].strftime('%Y-%m-%d')
        if date not in history:
            continue

        dives = history[date]
        if len(dives) > 1:
            dive = dives.pop(0)
        else:
            dive = dives[0]

        info['site'] = dive
        info['directory'] = f'{date} {dive}'
        yield info


def _parse_number(tree: lxml.etree, path: str) -> float:  # type: ignore
    return tree.xpath(f'number({path})', namespaces=NAMESPACES)


NAMESPACES = {'uddf': 'http://www.streit.cc/uddf/3.2/'}
