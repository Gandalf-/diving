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
from util import static
from util.metrics import metrics
from util.common import meters_to_feet, pascal_to_psi, kelvin_to_fahrenheit

DiveInfo = Dict[str, Any]

root = '/Users/leaf/working/dives/Perdix/'


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
        metrics.counter('uddf dives without pressure')
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
    dives_without_computer = ('5 Ari South Maihi Beyru',)
    history: Dict[str, List[str]] = {}

    for dive in [os.path.basename(dive) for dive in collection.dive_listing()]:
        date, name = dive.split(' ', 1)
        if name in dives_without_computer:
            continue
        history.setdefault(date, [])
        history[date].append(name)

    return history


def update(info: DiveInfo, directory: str) -> DiveInfo:
    _, name = directory.split(' ', 1)
    dive = {k: v for k, v in info.items()}
    dive['site'] = name
    dive['directory'] = directory

    metrics.counter('uddf dives matched')
    return dive


def match_dive_info(infos: Iterator[DiveInfo]) -> Iterator[DiveInfo]:
    history = build_dive_history()

    for info in sorted(infos, key=lambda i: i['number']):
        if info['number'] in static.dives:
            yield update(info, static.dives[info['number']])
            continue

        date = info['date'].strftime('%Y-%m-%d')
        if date not in history:
            metrics.counter('uddf dives without match')
            continue

        dirs = history[date]
        # TODO should just be dirs.pop(0) always, but that breaks, suspicous
        if len(dirs) > 1:
            directory = dirs.pop(0)
        else:
            directory = dirs[0]

        yield update(info, f'{date} {directory}')


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

MALDIVES = {
    120: '2022-11-12 2 Male North Manta Point',
    119: '2022-11-12 1 Male South Kuda Giri Wreck',
    118: '2022-11-11 3 Male South Vilivaru Giri',
    117: '2022-11-11 2 Vaavu Dhiggiri Giri',
    116: '2022-11-11 1 Ari South Kudhi Maa Wreck',
    115: '2022-11-10 4 Ari South Maihi Beyru',
    114: '2022-11-10 3 Ari South Rangali Madivaru',
    113: '2022-11-10 2 Ari South Sun Island Beyru',
    112: '2022-11-10 1 Ari South Seventh Heaven',
    111: '2022-11-09 3 Ari South Kudarah Thila',
    110: '2022-11-09 2 Ari South Lily Bay',
    109: '2022-11-09 1 Ari North Fish Head',
    108: '2022-11-08 4 Ari North Fesdu Lagoon',
    107: '2022-11-08 3 Ari North Hohola Thila',
    106: '2022-11-08 2 Ari North Bathala Thila',
    105: '2022-11-08 1 Rasdhoo Madivaru',
    104: '2022-11-07 3 Male North Fish Factory',
    103: '2022-11-07 2 Male North Manta Point',
    102: '2022-11-07 1 Male North Kurumba',
}
