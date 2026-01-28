#!/usr/bin/python3

"""
Parsing UDDF files

https://www.streit.cc/extern/uddf_v321/en/index.html
"""

import math
import os
from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache
from typing import Any, TypeAlias

import lxml.etree
from frozendict import frozendict

from diving.util import collection, database, static
from diving.util.common import Counter, kelvin_to_fahrenheit, meters_to_feet, pascal_to_psi
from diving.util.freeze import deep_freeze
from diving.util.metrics import metrics

# PUBLIC

DiveInfo: TypeAlias = dict[str, Any]


def calculate_sac(pressure_drop_psi: float, depth_feet: float, time_seconds: float) -> float:
    """Calculate SAC rate (PSI/min at surface equivalent).

    Args:
        pressure_drop_psi: Pressure consumed during interval (PSI)
        depth_feet: Average depth during interval (feet)
        time_seconds: Duration of interval (seconds)

    Returns:
        SAC rate in PSI/min normalized to surface pressure
    """
    if time_seconds <= 0 or pressure_drop_psi <= 0:
        return 0.0
    ata = (depth_feet / 33) + 1
    time_minutes = time_seconds / 60
    return (pressure_drop_psi / time_minutes) / ata


FrozenDiveInfo: TypeAlias = frozendict[str, Any]


def all() -> frozendict[str, FrozenDiveInfo]:
    return _matched_dives()


def lookup(dive: str) -> FrozenDiveInfo | None:
    # this should be the exact directory
    return _matched_dives().get(dive)


def search(date: str, hint: str) -> FrozenDiveInfo | None:
    dates_only: dict[str, list[str]] = {}
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


def dive_info_html(info: DiveInfo | FrozenDiveInfo) -> str:
    """build a snippet from the dive computer information available"""
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
    return f"""\
<p class="center">{' &nbsp; '.join(parts)}</p>
"""


# PRIVATE


_UDDF_ROOT = '/Users/leaf/working/diving/logs/'
_XML_NS = {'uddf': 'http://www.streit.cc/uddf/3.2/'}


suunto_counter = Counter()


def _parse_number(tree: Any, path: str) -> float:  # type: ignore
    return tree.xpath(f'number({path})', namespaces=_XML_NS)


@lru_cache(None)
def _parse(file: str) -> FrozenDiveInfo:
    info = _db_decode(database.database.get('diving', 'log', 'cache', file))
    if not info:
        parser = _parse_uddf if file.endswith('.uddf') else _parse_sml
        info = parser(file)
        database.database.set('diving', 'log', 'cache', file, value=_db_encode(info))
    return deep_freeze(info)


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
        tree.xpath('//uddf:informationbeforedive/uddf:datetime/text()', namespaces=_XML_NS)[0]
    )

    number = _parse_number(tree, '//uddf:informationbeforedive/uddf:divenumber')
    max_depth = _parse_number(tree, '//uddf:informationafterdive/uddf:greatestdepth')
    duration = _parse_number(tree, '//uddf:informationafterdive/uddf:diveduration')

    # Extract waypoint data: depth, time, temperature, tank pressure
    waypoints = tree.xpath('//uddf:waypoint', namespaces=_XML_NS)
    depths: list[tuple[float, float]] = []
    sacs: list[float] = []
    tank_start = float('nan')
    tank_end = float('nan')
    temp_high = 0.0
    temp_low = 9999.0

    # Collect per-waypoint data
    waypoint_data: list[tuple[float, float, float]] = []  # (depth_feet, time_sec, pressure_psi)
    for wp in waypoints:
        depth_m = float(wp.xpath('uddf:depth/text()', namespaces=_XML_NS)[0])
        depth_ft = meters_to_feet(depth_m)
        time_sec = float(wp.xpath('uddf:divetime/text()', namespaces=_XML_NS)[0])

        # Tank pressure (T1)
        pressure_elements = wp.xpath('uddf:tankpressure[@ref="T1"]/text()', namespaces=_XML_NS)
        pressure_pa = float(pressure_elements[0]) if pressure_elements else 0.0
        pressure_psi = pascal_to_psi(pressure_pa) if pressure_pa > 100 else 0.0

        # Track tank start/end
        if pressure_pa > 100:
            if math.isnan(tank_start):
                tank_start = pressure_pa
            tank_end = pressure_pa

        # Temperature
        temp_elements = wp.xpath('uddf:temperature/text()', namespaces=_XML_NS)
        if temp_elements:
            temp_k = float(temp_elements[0])
            temp_high = max(temp_high, temp_k)
            temp_low = min(temp_low, temp_k)

        waypoint_data.append((depth_ft, time_sec, pressure_psi))

    # Build depths list (normalized position)
    for idx, (d_ft, _, _) in enumerate(waypoint_data):
        position = (idx + 1) / len(waypoint_data)
        depths.append((position, d_ft))

    # Calculate SAC for each interval
    for i in range(len(waypoint_data) - 1):
        depth1, time1, pressure1 = waypoint_data[i]
        depth2, time2, pressure2 = waypoint_data[i + 1]

        # Skip if missing pressure data, shallows, or in first 3 minutes
        if pressure1 <= 0 or pressure2 <= 0:
            continue
        if depth1 < 10 or depth2 < 10:
            continue
        if time1 < 180:
            continue

        avg_depth = (depth1 + depth2) / 2
        interval = time2 - time1
        pressure_drop = pressure1 - pressure2

        sac = calculate_sac(pressure_drop, avg_depth, interval)
        if 0 < sac < 75:
            sacs.append(sac)

    # Handle dives without transmitter (dives 0-2)
    if math.isnan(tank_start):
        metrics.counter('dive logs without pressure')
        tank_start = 0
        tank_end = 0

    return {
        'date': date,
        'number': 200 + int(number),
        'depth': meters_to_feet(max_depth),
        'depths': depths,
        'sacs': sacs,
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
    date_str = root.xpath('./sml:DeviceLog/sml:Header/sml:DateTime/text()', namespaces=ns)[0]
    depth = root.xpath('./sml:DeviceLog/sml:Header/sml:Depth/sml:Max/text()', namespaces=ns)[0]
    duration = root.xpath('./sml:DeviceLog/sml:Header/sml:Duration/text()', namespaces=ns)[0]
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
        'sacs': [],
        'duration': int(duration),
        'tank_start': pascal_to_psi(int(tank_start)),
        'tank_end': pascal_to_psi(int(tank_end)),
        'temp_high': kelvin_to_fahrenheit(max(temp_start, temp_dive)),
        'temp_low': kelvin_to_fahrenheit(min(temp_start, temp_dive)),
    }


def _load_dive_info() -> Iterator[FrozenDiveInfo]:
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


def _build_dive_history() -> dict[str, list[str]]:
    """No caching possible here since the consumer modifies the result to
    track progress through multi-dive days. Plus, dive_listing is already cached
    """
    history: dict[str, list[str]] = {}

    for dive in [os.path.basename(dive) for dive in collection.dive_listing()]:
        date, name = dive.split(' ', 1)
        if name in static.dives_without_computer:
            continue
        history.setdefault(date, [])
        history[date].append(name)

    return history


def _update_info(info: DiveInfo | FrozenDiveInfo, directory: str) -> DiveInfo:
    _, name = directory.split(' ', 1)
    dive = {k: v for k, v in info.items()}
    dive['site'] = name
    dive['directory'] = directory

    metrics.counter('dive logs matched')
    return dive


def _match_dive_info(infos: Iterator[FrozenDiveInfo]) -> Iterator[DiveInfo]:
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

        if directory in static.dives_without_computer:
            continue

        yield _update_info(info, f'{date} {directory}')


@lru_cache(None)
def _matched_dives() -> frozendict[str, FrozenDiveInfo]:
    dives: dict[str, DiveInfo] = {}
    for dive in _match_dive_info(_load_dive_info()):
        dives[dive['directory']] = dive
    return deep_freeze(dives)
