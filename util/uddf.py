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

# PUBLIC

DiveInfo = Dict[str, Any]


def lookup(dive: str) -> Optional[DiveInfo]:
    return _matched_dives().get(dive)


def search(date: str, hint: str) -> Optional[DiveInfo]:
    dates_only: Dict[str, List[str]] = {}
    for dive in _matched_dives():
        _date, _ = dive.split(' ', 1)
        dates_only.setdefault(_date, [])
        dates_only[_date].append(dive)

    try:
        dive = next(dive for dive in dates_only.get(date, []) if hint in dive)
        return lookup(dive)
    except StopIteration:
        return None


def dive_info_html(info: DiveInfo) -> str:
    '''build a snippet from the dive computer information available'''
    parts = []
    parts.append(f'{info["depth"]}\'')
    parts.append(f'{info["duration"] // 60}min')

    temp_high = info['temp_high']
    temp_low = info['temp_low']
    if temp_low <= temp_high:
        parts.append(f'{temp_low}&rarr;{temp_high}&deg;F')

    start = info['tank_start']
    end = info['tank_end']
    if start != 0 and end != 0:
        parts.append(f'{start}&rarr;{end} PSI')

    metrics.counter('uddf html snippets added')
    return f'''\
<p class="tight">{' &nbsp; '.join(parts)}</p>
'''


# PRIVATE


_UDDF_ROOT = '/Users/leaf/working/dives/Perdix/'
_XML_NS = {'uddf': 'http://www.streit.cc/uddf/3.2/'}


def _parse_number(tree: Any, path: str) -> float:  # type: ignore
    return tree.xpath(f'number({path})', namespaces=_XML_NS)


@lru_cache(None)
def _parse(file: str) -> DiveInfo:
    tree = lxml.etree.parse(os.path.join(_UDDF_ROOT, file))  # type: ignore

    date = datetime.fromisoformat(
        tree.xpath(
            '//uddf:informationbeforedive/uddf:datetime/text()', namespaces=_XML_NS
        )[0]
    )

    number = _parse_number(tree, '//uddf:informationbeforedive/uddf:divenumber')
    depth = _parse_number(tree, '//uddf:informationafterdive/uddf:greatestdepth')
    duration = _parse_number(tree, '//uddf:informationafterdive/uddf:diveduration')

    tank_start = float('nan')
    tank_end = float('nan')
    for start in tree.xpath(
        '//uddf:waypoint/uddf:tankpressure[@ref="T1"]', namespaces=_XML_NS
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
    for temp in tree.xpath('//uddf:waypoint/uddf:temperature', namespaces=_XML_NS):
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


def _load_dive_info() -> Iterator[DiveInfo]:
    for candidate in os.listdir(_UDDF_ROOT):
        if not candidate.endswith('.uddf'):
            continue

        info = _parse(candidate)
        if info['duration'] <= 900:
            continue
        if info['depth'] <= 10:
            continue

        yield info


def _build_dive_history() -> Dict[str, List[str]]:
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


def _update_info(info: DiveInfo, directory: str) -> DiveInfo:
    _, name = directory.split(' ', 1)
    dive = {k: v for k, v in info.items()}
    dive['site'] = name
    dive['directory'] = directory

    metrics.counter('uddf dives matched')
    return dive


def _match_dive_info(infos: Iterator[DiveInfo]) -> Iterator[DiveInfo]:
    history = _build_dive_history()

    for info in sorted(infos, key=lambda i: i['number']):
        if info['number'] in static.dives:
            yield _update_info(info, static.dives[info['number']])
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

        yield _update_info(info, f'{date} {directory}')


@lru_cache(None)
def _matched_dives() -> Dict[str, DiveInfo]:
    dives = {}
    for dive in _match_dive_info(_load_dive_info()):
        dives[dive['directory']] = dive
    return dives
