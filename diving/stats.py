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
from collections.abc import Iterable, Sequence
from typing import Any, TypeAlias

from diving import locations
from diving.util import log
from diving.util.resource import VersionedResource
from diving.util.static import source_root, stylesheet

# Type aliases
StatsBundle: TypeAlias = dict[str, Any]
Record: TypeAlias = dict[str, Any]
Distribution: TypeAlias = list[list[int | float]]
LocationStats: TypeAlias = dict[str, dict[str, int | float]]
DiveData: TypeAlias = log.DiveInfo | log.FrozenDiveInfo


def get_all_dives() -> Iterable[log.FrozenDiveInfo]:
    """Retrieve all matched dives from the log module."""
    return log._matched_dives().values()


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
        'dive': deepest.get('site', ''),
        'date': deepest['date'].strftime('%Y-%m-%d'),
    }

    # Longest dive
    longest = max(dives, key=lambda d: d['duration'])
    records['longest'] = {
        'value': longest['duration'] // 60,
        'unit': 'min',
        'dive': longest.get('site', ''),
        'date': longest['date'].strftime('%Y-%m-%d'),
    }

    # Coldest dive
    coldest = min(dives, key=lambda d: d['temp_low'])
    records['coldest'] = {
        'value': coldest['temp_low'],
        'unit': '°F',
        'dive': coldest.get('site', ''),
        'date': coldest['date'].strftime('%Y-%m-%d'),
    }

    # Most dives in a single day
    dates = [d['date'].strftime('%Y-%m-%d') for d in dives]
    date_counts = Counter(dates)
    if date_counts:
        most_day, count = date_counts.most_common(1)[0]
        records['most_dives_day'] = {
            'value': count,
            'unit': 'dives',
            'dive': '',
            'date': most_day,
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
        if count > 0:
            result.append([start, start + bucket_size, count])

    return result


def build_distributions(dives: Sequence[DiveData]) -> dict[str, Distribution]:
    """Build all distribution histograms."""
    depths = [d['depth'] for d in dives]
    durations = [d['duration'] / 60 for d in dives]  # Convert to minutes
    temps = [d['temp_low'] for d in dives]

    return {
        'depth': build_distribution(depths, 10),  # 10ft buckets
        'duration': build_distribution(durations, 15),  # 15min buckets
        'temperature': build_distribution(temps, 10),  # 10°F buckets
    }


def build_location_stats(dives: Sequence[DiveData]) -> LocationStats:
    """Aggregate statistics by region."""
    region_data: dict[str, dict[str, list[float]]] = {}

    for dive in dives:
        site = dive.get('site', '')
        if not site:
            continue

        try:
            region = locations.get_region(site)
        except AssertionError:
            continue

        if region not in region_data:
            region_data[region] = {'depths': [], 'temps': [], 'count': []}

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


def build_totals(dives: Sequence[DiveData]) -> dict[str, int | float]:
    """Compute aggregate totals."""
    total_time = sum(d['duration'] for d in dives)
    sites = set(d.get('site', '') for d in dives if d.get('site'))

    return {
        'dive_count': len(dives),
        'total_bottom_time_hours': round(total_time / 3600, 1),
        'deepest_depth': max((d['depth'] for d in dives), default=0),
        'unique_sites': len(sites),
    }


def build_stats_bundle() -> StatsBundle:
    """Build the complete stats data bundle."""
    dives = list(get_all_dives())

    return {
        'records': build_records(dives),
        'distributions': build_distributions(dives),
        'locations': build_location_stats(dives),
        'totals': build_totals(dives),
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
        os.path.join(source_root, 'web', 'stats.js'),
        'stats/stats.js',
    )

    data = VersionedResource('stats/data.js', 'stats')
    stats_js = VersionedResource('stats/stats.js', 'stats')

    # Write index.html
    with open('stats/index.html', 'w+') as fd:
        html = _html_builder(stylesheet.path, stats_js.path, data.path)
        print(html, file=fd, end='')


def _html_builder(css: str, stats_js: str, data_js: str) -> str:
    """Build the stats page HTML."""
    desc = 'Scuba diving statistics: personal records, dive distributions, and location analytics'
    # Carousel order: Timeline, Gallery, Detective, Sites, Stats, Taxonomy
    # Stats is at index 4, so we show: Detective, Sites, Stats, Taxonomy, Timeline
    return f"""\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Dive Stats</title>
        <link rel="canonical" href="https://diving.anardil.net/stats/" />
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="{desc}">
        <link rel="stylesheet" href="/{css}" />
        <script src="/{data_js}"></script>
        <script src="/{stats_js}" defer></script>
        <style>
body {{
    max-width: 1080px;
    margin-left: auto;
    margin-right: auto;
    float: none !important;
}}
.stats-section {{
    margin: 2em 1em;
    clear: both;
}}
.stats-section h2 {{
    margin-bottom: 1em;
    text-align: center;
}}
.records-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1em;
    margin: 1em 0;
}}
.record-card {{
    background: var(--nav-pill-bg, #f0f0f0);
    border-radius: 8px;
    padding: 1em;
    text-align: center;
}}
.record-card .label {{
    font-size: 0.9em;
    opacity: 0.8;
    margin-bottom: 0.5em;
}}
.record-card .value {{
    font-size: 2em;
    font-weight: bold;
}}
.record-card .context {{
    font-size: 0.8em;
    opacity: 0.7;
    margin-top: 0.5em;
}}
.chart-container {{
    margin: 1em 0;
    min-height: 100px;
}}
.locations-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}}
.locations-table th,
.locations-table td {{
    padding: 0.5em 1em;
    text-align: left;
    border-bottom: 1px solid var(--border-color, #ccc);
}}
.locations-table th {{
    background: var(--nav-pill-bg, #f0f0f0);
}}
.totals-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1em;
    margin: 1em 0;
    text-align: center;
}}
.total-item .value {{
    font-size: 2.5em;
    font-weight: bold;
    color: #fff;
}}
.total-item .label {{
    font-size: 0.9em;
    opacity: 0.8;
    color: #fff;
}}
.locations-table td {{
    color: #fff;
}}
        </style>
    </head>

    <body>
        <div class="wrapper">
            <div class="title">
                <a href="/detective/">
                    <h1 class="nav-pill active detective">🔍</h1>
                </a>
                <div class="nav-pill spacer"></div>
                <a href="/sites/">
                    <h1 class="nav-pill active sites">🌎</h1>
                </a>
                <div class="nav-pill spacer"></div>
                <a href="/stats/">
                    <h1 class="nav-pill active">Stats</h1>
                </a>
                <div class="nav-pill spacer"></div>
                <a href="/taxonomy/">
                    <h1 class="nav-pill active taxonomy">🔬</h1>
                </a>
                <div class="nav-pill spacer"></div>
                <a href="/timeline/">
                    <h1 class="nav-pill active timeline">📅</h1>
                </a>
                <p class="scientific"></p>
            </div>

            <div class="stats-section" id="totals-section">
                <h2>Totals</h2>
                <div class="totals-grid" id="totals"></div>
            </div>

            <div class="stats-section" id="records-section">
                <h2>Personal Records</h2>
                <div class="records-grid" id="records"></div>
            </div>

            <div class="stats-section" id="depth-section">
                <h2>Depth Distribution</h2>
                <div class="chart-container" id="depth-chart"></div>
            </div>

            <div class="stats-section" id="duration-section">
                <h2>Duration Distribution</h2>
                <div class="chart-container" id="duration-chart"></div>
            </div>

            <div class="stats-section" id="temp-section">
                <h2>Temperature Distribution</h2>
                <div class="chart-container" id="temp-chart"></div>
            </div>

            <div class="stats-section" id="locations-section">
                <h2>Locations</h2>
                <table class="locations-table" id="locations"></table>
            </div>
        </div>
    </body>
</html>
"""
