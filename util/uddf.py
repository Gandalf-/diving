#!/usr/bin/python3

'''
Parsing UDDF files

https://www.streit.cc/extern/uddf_v321/en/index.html
'''

import os
import math
from functools import lru_cache
from typing import Dict, Any, Iterator, List, Optional
from datetime import datetime

import lxml

from util import collection

DiveInfo = Dict[str, Any]

root = '/Users/leaf/Desktop/Perdix/'


def meters_to_feet(m: float) -> int:
    return int(m * 3.28084)


def pascal_to_psi(m: float) -> int:
    return int(m * 0.000145038)


def kelvin_to_fahrenheit(m: float) -> int:
    return int((m - 273.15) * 1.8 + 32)


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

    tank_start = float('nan')
    tank_end = float('nan')
    for start in tree.xpath(
        '//uddf:waypoint/uddf:tankpressure[@ref="T1"]', namespaces=NAMESPACES
    ):
        value = float(start.text)
        last = value
        if value > 100 and math.isnan(tank_start):
            tank_start = value

    if not math.isnan(tank_start):
        tank_end = last
    else:
        tank_start = 0
        tank_end = 0

    temp_high = 0.0
    temp_low = 9999.0
    for temp in tree.xpath('//uddf:waypoint/uddf:temperature', namespaces=NAMESPACES):
        value = float(temp.text)
        temp_high = max(temp_high, value)
        temp_low = min(temp_low, value)

    return {
        'date': date,
        'number': int(number),
        'depth': meters_to_feet(depth),
        'duration': int(duration),
        'tank_start': pascal_to_psi(tank_start),
        'tank_end': pascal_to_psi(tank_end),
        'temp_high': kelvin_to_fahrenheit(temp_high),
        'temp_low': kelvin_to_fahrenheit(temp_low),
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

        dirs = history[date]
        if len(dirs) > 1:
            directory = dirs.pop(0)
        else:
            directory = dirs[0]

        dive = {k: v for k, v in info.items()}
        dive['site'] = directory
        dive['directory'] = f'{date} {directory}'
        yield dive


def lookup(dive: str) -> Optional[DiveInfo]:
    return _matched_dives().get(dive)


@lru_cache(None)
def _matched_dives() -> Dict[str, DiveInfo]:
    dives = {}
    for dive in match_dive_info(load_dive_info()):
        dives[dive['directory']] = dive
    return dives


def _parse_number(tree: lxml.etree, path: str) -> float:  # type: ignore
    return tree.xpath(f'number({path})', namespaces=NAMESPACES)


NAMESPACES = {'uddf': 'http://www.streit.cc/uddf/3.2/'}
