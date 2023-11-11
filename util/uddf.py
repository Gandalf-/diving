#!/usr/bin/python3

'''
Parsing UDDF files

https://www.streit.cc/extern/uddf_v321/en/index.html
'''

import math
import os
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Optional

import lxml

from util import collection, database, static
from util.common import Counter, kelvin_to_fahrenheit, meters_to_feet, pascal_to_psi
from util.metrics import metrics

# PUBLIC

DiveInfo = Dict[str, Any]


def lookup(dive: str) -> Optional[DiveInfo]:
    # this should be the exact directory
    return _matched_dives().get(dive)


def search(date: str, hint: str) -> Optional[DiveInfo]:
    dates_only: Dict[str, List[str]] = {}
    for dive in _matched_dives():
        ymd, _ = dive.split(' ', 1)
        dates_only.setdefault(ymd, [])
        dates_only[ymd].append(dive)

    try:
        dive = next(dive for dive in dates_only.get(date, []) if hint in dive)
        return lookup(dive)
    except StopIteration:
        time = datetime.strptime(date, '%Y-%m-%d')
        first_perdix_dive = datetime.strptime('2021-08-13', '%Y-%m-%d')

        if time > first_perdix_dive:
            metrics.counter('dive logs missing that should exist')

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

    metrics.counter('dive log html snippets added')
    return f'''\
<p class="tight">{' &nbsp; '.join(parts)}</p>
'''


def series_match(series: List[int], others: List[int], target: int) -> int:
    assert target in others

    position = others.index(target)
    step_size = len(series) / len(others)

    index = round(position * step_size)
    return series[index]


# PRIVATE


_UDDF_ROOT = '/Users/leaf/working/dives/'
_XML_NS = {'uddf': 'http://www.streit.cc/uddf/3.2/'}


suunto_counter = Counter()


def _parse_number(tree: Any, path: str) -> float:  # type: ignore
    return tree.xpath(f'number({path})', namespaces=_XML_NS)


@lru_cache(None)
def _parse(file: str) -> DiveInfo:
    info = _db_decode(database.database.get('diving', 'log', 'cache', file))
    if not info:
        parser = _parse_uddf if file.endswith('.uddf') else _parse_sml
        info = parser(file)
        database.database.set('diving', 'log', 'cache', file, value=_db_encode(info))
    return info


def _db_encode(info: DiveInfo) -> DiveInfo:
    if not info:
        return {}
    encoded = {k: v for k, v in info.items()}
    encoded['date'] = datetime.isoformat(info['date'])
    return encoded


def _db_decode(encoded: DiveInfo) -> DiveInfo:
    if not encoded:
        return {}
    info = {k: v for k, v in encoded.items()}
    info['date'] = datetime.fromisoformat(encoded['date'])
    return info


def _parse_uddf(file: str) -> DiveInfo:
    tree = lxml.etree.parse(os.path.join(_UDDF_ROOT, 'Perdix', file))  # type: ignore

    date = datetime.fromisoformat(
        tree.xpath(
            '//uddf:informationbeforedive/uddf:datetime/text()', namespaces=_XML_NS
        )[0]
    )

    number = _parse_number(tree, '//uddf:informationbeforedive/uddf:divenumber')
    max_depth = _parse_number(tree, '//uddf:informationafterdive/uddf:greatestdepth')
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
        # This accounts for dives 0-2 which didn't have a transmitter
        metrics.counter('dive logs without pressure')
        tank_start = 0
        tank_end = 0

    temp_high = 0.0
    temp_low = 9999.0
    for temp in tree.xpath('//uddf:waypoint/uddf:temperature', namespaces=_XML_NS):
        value = float(temp.text)
        temp_high = max(temp_high, value)
        temp_low = min(temp_low, value)

    timeseries = tree.xpath('//uddf:waypoint/uddf:depth', namespaces=_XML_NS)
    depths = []

    # Iterate over each waypoint and extract depth data
    for index, depth in enumerate(timeseries):
        depth_meters = float(depth.text)
        depth_feet = meters_to_feet(depth_meters)
        position = (index + 1) / len(timeseries)
        depths.append((position, depth_feet))

    return {
        'date': date,
        'number': 200 + int(number),
        'depth': meters_to_feet(max_depth),
        'depths': depths,
        'duration': int(duration),
        'tank_start': pascal_to_psi(tank_start),
        'tank_end': pascal_to_psi(tank_end),
        'temp_high': kelvin_to_fahrenheit(temp_high),
        'temp_low': kelvin_to_fahrenheit(temp_low),
    }


def _parse_sml(file: str) -> DiveInfo:
    root = lxml.etree.parse(os.path.join(_UDDF_ROOT, 'Suunto', file))  # type: ignore

    # Define the XML namespace
    ns = {'sml': 'http://www.suunto.com/schemas/sml'}

    # Extract data from XML using XPath
    date_str = root.xpath(
        './sml:DeviceLog/sml:Header/sml:DateTime/text()', namespaces=ns
    )[0]
    depth = root.xpath(
        './sml:DeviceLog/sml:Header/sml:Depth/sml:Max/text()', namespaces=ns
    )[0]
    duration = root.xpath(
        './sml:DeviceLog/sml:Header/sml:Duration/text()', namespaces=ns
    )[0]
    tank_start = root.xpath(
        './sml:DeviceLog/sml:Header/sml:Diving/sml:Gases/sml:Gas/sml:StartPressure/text()',
        namespaces=ns,
    )[0]
    tank_end = root.xpath(
        './sml:DeviceLog/sml:Header/sml:Diving/sml:Gases/sml:Gas/sml:EndPressure/text()',
        namespaces=ns,
    )[0]
    temp_start = float(
        root.xpath(
            './sml:DeviceLog/sml:Header/sml:Diving/sml:TempAtStart/text()',
            namespaces=ns,
        )[0]
    )
    temp_dive = float(
        root.xpath(
            './sml:DeviceLog/sml:Header/sml:Diving/sml:TempAtMaxDepth/text()',
            namespaces=ns,
        )[0]
    )

    return {
        'date': datetime.fromisoformat(date_str),
        'number': suunto_counter.next(),
        'depth': meters_to_feet(float(depth)),
        'depths': [],
        'duration': int(duration),
        'tank_start': pascal_to_psi(int(tank_start)),
        'tank_end': pascal_to_psi(int(tank_end)),
        'temp_high': kelvin_to_fahrenheit(max(temp_start, temp_dive)),
        'temp_low': kelvin_to_fahrenheit(min(temp_start, temp_dive)),
    }


def _load_dive_info() -> Iterator[DiveInfo]:
    log_types = [('Perdix', '.uddf'), ('Suunto', '.sml')]

    def candidates() -> Iterator[str]:
        for directory, extension in log_types:
            for candidate in os.listdir(os.path.join(_UDDF_ROOT, directory)):
                assert candidate.endswith(extension)
                yield candidate

    for candidate in candidates():
        info = _parse(candidate)
        if info['duration'] <= 900:
            continue
        if info['depth'] <= 10:
            continue
        if info['number'] in static.dives_without_camera:
            continue

        yield info


def _build_dive_history() -> Dict[str, List[str]]:
    '''No caching possible here since the consumer modifies the result to
    track progress through multi-dive days. Plus, dive_listing is already cached
    '''
    history: Dict[str, List[str]] = {}

    for dive in [os.path.basename(dive) for dive in collection.dive_listing()]:
        date, name = dive.split(' ', 1)
        if name in static.dives_without_computer:
            continue
        history.setdefault(date, [])
        history[date].append(name)

    return history


def _update_info(info: DiveInfo, directory: str) -> DiveInfo:
    _, name = directory.split(' ', 1)
    dive = {k: v for k, v in info.items()}
    dive['site'] = name
    dive['directory'] = directory

    metrics.counter('dive logs matched')
    return dive


def _match_dive_info(infos: Iterator[DiveInfo]) -> Iterator[DiveInfo]:
    history = _build_dive_history()

    for info in sorted(infos, key=lambda i: i['number']):
        if info['number'] in static.dives:
            yield _update_info(info, static.dives[info['number']])
            continue

        date = info['date'].strftime('%Y-%m-%d')
        if date not in history:
            continue

        dirs = history[date]
        assert dirs, f'dive {info["number"]} on {date} may be a no camera dive'
        directory = dirs.pop(0)

        yield _update_info(info, f'{date} {directory}')


@lru_cache(None)
def _matched_dives() -> Dict[str, DiveInfo]:
    dives = {}
    for dive in _match_dive_info(_load_dive_info()):
        dives[dive['directory']] = dive
    return dives
