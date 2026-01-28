#!/usr/bin/python3

"""
Dive statistics aggregation and display.

Extracts statistics from dive logs and generates a stats page with:
- Personal records (deepest, longest, coldest dives)
- Distribution histograms (depth, duration, temperature)
- Location analytics (dives per region)
"""

import json
import os
import shutil
from collections import Counter
from collections.abc import Sequence
from typing import Any, TypeAlias

from diving import locations
from diving.hypertext import Where, navigation_carousel
from diving.util import log, static
from diving.util.collection import dive_listing
from diving.util.image import dive_to_location
from diving.util.resource import VersionedResource

# Type aliases
StatsBundle: TypeAlias = dict[str, Any]
Record: TypeAlias = dict[str, Any]
Distribution: TypeAlias = list[list[int | float]]
LocationStats: TypeAlias = dict[str, dict[str, int | float]]
DiveData: TypeAlias = log.DiveInfo | log.FrozenDiveInfo


def _make_sites_link(dive: DiveData) -> str:
    """Build a sites link from dive data, or empty string if not possible."""
    site = dive_to_location(dive['directory'])
    date = dive['date'].strftime('%Y-%m-%d')
    return locations.sites_link(date, site)


def build_records(dives: Sequence[DiveData]) -> dict[str, Record]:
    """Compute personal records from dive data."""
    if not dives:
        return {}

    records: dict[str, Record] = {}

    # Deepest dive
    deepest = max(dives, key=lambda d: d['depth'])
    records['deepest'] = {
        'value': deepest['depth'],
        'unit': 'ft',
        'dive': dive_to_location(deepest['directory']),
        'date': deepest['date'].strftime('%Y-%m-%d'),
        'link': _make_sites_link(deepest),
    }

    # Longest dive
    longest = max(dives, key=lambda d: d['duration'])
    records['longest'] = {
        'value': longest['duration'] // 60,
        'unit': 'min',
        'dive': dive_to_location(longest['directory']),
        'date': longest['date'].strftime('%Y-%m-%d'),
        'link': _make_sites_link(longest),
    }

    # Shallowest dive
    shallowest = min(dives, key=lambda d: d['depth'])
    records['shallowest'] = {
        'value': shallowest['depth'],
        'unit': 'ft',
        'dive': dive_to_location(shallowest['directory']),
        'date': shallowest['date'].strftime('%Y-%m-%d'),
        'link': _make_sites_link(shallowest),
    }

    # Shortest dive
    shortest = min(dives, key=lambda d: d['duration'])
    records['shortest'] = {
        'value': shortest['duration'] // 60,
        'unit': 'min',
        'dive': dive_to_location(shortest['directory']),
        'date': shortest['date'].strftime('%Y-%m-%d'),
        'link': _make_sites_link(shortest),
    }

    # Coldest dive
    coldest = min(dives, key=lambda d: d['temp_low'])
    records['coldest'] = {
        'value': coldest['temp_low'],
        'unit': '°F',
        'dive': dive_to_location(coldest['directory']),
        'date': coldest['date'].strftime('%Y-%m-%d'),
        'link': _make_sites_link(coldest),
    }

    # Warmest dive
    warmest = max(dives, key=lambda d: d['temp_low'])
    records['warmest'] = {
        'value': warmest['temp_low'],
        'unit': '°F',
        'dive': dive_to_location(warmest['directory']),
        'date': warmest['date'].strftime('%Y-%m-%d'),
        'link': _make_sites_link(warmest),
    }

    # Most dives in a single day
    dates = [d['date'].strftime('%Y-%m-%d') for d in dives]
    date_counts = Counter(dates)
    if date_counts:
        most_day, count = date_counts.most_common(1)[0]
        # Find first dive on that day (by directory order)
        day_dives = [d for d in dives if d['date'].strftime('%Y-%m-%d') == most_day]
        first_dive = min(day_dives, key=lambda d: d.get('directory', ''))
        records['most_dives_day'] = {
            'value': count,
            'unit': 'dives',
            'dive': '',
            'date': most_day,
            'link': _make_sites_link(first_dive),
        }

    return records


def build_distribution(values: list[float], bucket_size: int) -> Distribution:
    """Create histogram buckets from a list of values.

    Returns list of [min, max, count] for each bucket.
    """
    if not values:
        return []

    min_val = int(min(values) // bucket_size) * bucket_size
    max_val = int(max(values) // bucket_size + 1) * bucket_size

    buckets: dict[int, int] = {}
    for v in values:
        bucket = int(v // bucket_size) * bucket_size
        buckets[bucket] = buckets.get(bucket, 0) + 1

    result: Distribution = []
    for start in range(min_val, max_val, bucket_size):
        count = buckets.get(start, 0)
        result.append([start, start + bucket_size, count])

    return result


def build_distributions(dives: Sequence[DiveData]) -> dict[str, Distribution]:
    """Build all distribution histograms."""
    depths = [d['depth'] for d in dives]
    durations = [d['duration'] / 60 for d in dives]  # Convert to minutes
    temps = [d['temp_low'] for d in dives]

    air_consumption = [
        d['tank_start'] - d['tank_end']
        for d in dives
        if d['tank_start'] > 0 and d['tank_end'] > 0 and d['tank_start'] > d['tank_end']
    ]
    sacs = [d['sacs'] for d in dives if d['sacs']]
    sacs = [sac for sublist in sacs for sac in sublist]

    return {
        'depth': build_distribution(depths, 10),  # 10ft buckets
        'duration': build_distribution(durations, 10),  # 10min buckets
        'temperature': build_distribution(temps, 5),  # 5°F buckets
        'air': build_distribution(air_consumption, 250),  # 250 PSI buckets
        'sac': build_distribution(sacs, 5),  # 5 PSI/min buckets
    }


def build_location_stats(dives: Sequence[DiveData]) -> LocationStats:
    """Aggregate statistics by region."""
    region_data: dict[str, dict[str, list[float]]] = {}

    for dive in dives:
        directory = dive.get('directory', '')
        if not directory:
            continue

        site = dive_to_location(directory)
        region = locations.get_region(site)

        region_data.setdefault(region, {'depths': [], 'temps': [], 'count': []})
        region_data[region]['depths'].append(dive['depth'])
        region_data[region]['temps'].append(dive['temp_low'])
        region_data[region]['count'].append(1)

    result: LocationStats = {}
    for region, data in region_data.items():
        result[region] = {
            'dives': len(data['count']),
            'avg_depth': round(sum(data['depths']) / len(data['depths'])) if data['depths'] else 0,
            'avg_temp': round(sum(data['temps']) / len(data['temps'])) if data['temps'] else 0,
        }

    return result


def build_totals(
    all_logged_dives: Sequence[DiveData], all_logged_photo_dives: Sequence[DiveData]
) -> dict[str, int | float]:
    """Compute aggregate totals."""
    total_time = sum(d['duration'] for d in all_logged_dives)
    sites = set(dive_to_location(d['directory']) for d in all_logged_photo_dives)

    logged_dives = len(all_logged_dives)
    photo_dives = len(dive_listing())
    logged_photo_dives = len(all_logged_photo_dives)

    total_dives = logged_dives
    total_dives += 150  # pre Perdix
    total_dives += len(static.dives_without_computer)
    total_dives += len(static.dives_without_camera)

    return {
        'total_dives': total_dives,
        'photo_dives': photo_dives,
        'logged_dives': logged_dives,
        'logged_photo_dives': logged_photo_dives,
        'total_bottom_time_hours': round(total_time / 3600, 1),
        'unique_sites': len(sites),
    }


def build_stats_bundle() -> StatsBundle:
    """Build the complete stats data bundle."""
    all_dives = log.all_dives()
    all_photo_dives = log.all_photo_dives()

    return {
        'records': build_records(all_photo_dives),
        'distributions': build_distributions(all_photo_dives),
        'locations': build_location_stats(all_photo_dives),
        'totals': build_totals(all_dives, all_photo_dives),
    }


def writer() -> None:
    """Write out all stats page artifacts."""
    os.makedirs('stats', exist_ok=True)

    bundle = build_stats_bundle()

    # Write data.js with embedded JSON
    with open('stats/data.js', 'w+') as fd:
        json_str = json.dumps(bundle, separators=(',', ':'))
        print(f'var stats_data = {json_str};', file=fd)

    # Copy stats.js
    shutil.copy(
        os.path.join(static.source_root, 'web', 'stats.js'),
        'stats/stats.js',
    )

    data = VersionedResource('stats/data.js', 'stats')
    stats_js = VersionedResource('stats/stats.js', 'stats')
    stats_css = VersionedResource(os.path.join(static.source_root, 'web/stats.css'), 'stats')

    # Write index.html
    with open('stats/index.html', 'w+') as fd:
        html = _html_builder(static.stylesheet.path, stats_css.path, stats_js.path, data.path)
        print(html, file=fd, end='')


def _html_builder(main_css: str, stats_css: str, stats_js: str, data_js: str) -> str:
    """Build the stats page HTML."""
    desc = 'Scuba diving statistics: personal records, dive distributions, and location analytics'
    nav = navigation_carousel(Where.Stats)
    return f"""\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Dive Stats</title>
        <link rel="canonical" href="https://diving.anardil.net/stats/" />
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="{desc}">
        <link rel="stylesheet" href="/{main_css}" />
        <link rel="stylesheet" href="/{stats_css}" />
        <script src="/{data_js}"></script>
        <script src="/{stats_js}" defer></script>
    </head>

    <body>
        <div class="wrapper">
            <div class="title">
{nav}
                <p class="scientific"></p>
            </div>

            <div class="stats-section" id="totals-section">
                <h2>Totals</h2>
                <div class="totals-grid" id="totals"></div>
            </div>

            <div class="stats-section" id="records-section">
                <h2>Records</h2>
                <div class="records-grid" id="records"></div>
            </div>

            <div class="stats-section" id="depth-section">
                <h2>Max Depth (ft)</h2>
                <div class="chart-container" id="depth-chart"></div>
            </div>

            <div class="stats-section" id="duration-section">
                <h2>Duration (mins)</h2>
                <div class="chart-container" id="duration-chart"></div>
            </div>

            <div class="stats-section" id="temp-section">
                <h2>Temperature (&deg;F)</h2>
                <div class="chart-container" id="temp-chart"></div>
            </div>

            <div class="stats-section" id="sac-section">
                <h2>Surface Air Consumption (PSI/min)</h2>
                <div class="chart-container" id="sac-chart"></div>
            </div>

            <div class="stats-section" id="air-section">
                <h2>Total Air Consumption (PSI)</h2>
                <div class="chart-container" id="air-chart"></div>
            </div>

            <div class="stats-section" id="locations-section">
                <h2>Locations</h2>
                <table class="locations-table" id="locations"></table>
            </div>
        </div>
    </body>
</html>
"""
