from datetime import datetime

from diving.stats import (
    build_distribution,
    build_distributions,
    build_location_stats,
    build_records,
    build_totals,
)


def make_dive(
    depth: int = 50,
    duration: int = 2400,
    temp_low: int = 55,
    temp_high: int = 60,
    date: str = '2023-01-01',
    site: str = 'Rockaway Beach',
    directory: str = '',
) -> dict:
    return {
        'depth': depth,
        'duration': duration,
        'temp_low': temp_low,
        'temp_high': temp_high,
        'date': datetime.fromisoformat(date),
        'site': site,
        'directory': directory or f'{date} {site}',
        'tank_start': 3000,
        'tank_end': 1000,
    }


class TestBuildRecords:
    def test_empty(self) -> None:
        assert build_records([]) == {}

    def test_single_dive(self) -> None:
        dives = [make_dive(depth=80, duration=3000, temp_low=48)]
        records = build_records(dives)

        assert records['deepest']['value'] == 80
        assert records['deepest']['unit'] == 'ft'
        assert records['longest']['value'] == 50  # 3000s / 60 = 50min
        assert records['coldest']['value'] == 48
        assert records['most_dives_day']['value'] == 1

    def test_multiple_dives(self) -> None:
        dives = [
            make_dive(depth=50, duration=2400, temp_low=55, date='2023-01-01'),
            make_dive(depth=100, duration=1800, temp_low=45, date='2023-01-02'),
            make_dive(depth=70, duration=3600, temp_low=60, date='2023-01-01'),
        ]
        records = build_records(dives)

        assert records['deepest']['value'] == 100
        assert records['deepest']['date'] == '2023-01-02'
        assert records['longest']['value'] == 60  # 3600s / 60
        assert records['coldest']['value'] == 45
        assert records['most_dives_day']['value'] == 2
        assert records['most_dives_day']['date'] == '2023-01-01'

    def test_record_context(self) -> None:
        dives = [make_dive(site='Rockaway Beach Deep Reef')]
        records = build_records(dives)

        assert records['deepest']['dive'] == 'Rockaway Beach Deep Reef'
        assert records['deepest']['date'] == '2023-01-01'

    def test_record_links(self) -> None:
        dives = [make_dive(site='Fort Ward', directory='2023-01-01 Fort Ward')]
        records = build_records(dives)

        assert records['deepest']['link'] == '/sites/Washington-Fort-Ward-2023-01-01'
        assert records['longest']['link'] == '/sites/Washington-Fort-Ward-2023-01-01'
        assert records['coldest']['link'] == '/sites/Washington-Fort-Ward-2023-01-01'
        assert records['most_dives_day']['link'] == '/sites/Washington-Fort-Ward-2023-01-01'

    def test_most_dives_day_links_to_first_dive(self) -> None:
        dives = [
            make_dive(date='2023-01-01', directory='2023-01-01 2 Rockaway'),
            make_dive(date='2023-01-01', directory='2023-01-01 1 Fort Ward'),
        ]
        records = build_records(dives)
        # Should link to first dive (1 Fort Ward), not second (2 Rockaway)
        assert records['most_dives_day']['link'] == '/sites/Washington-Fort-Ward-2023-01-01'


class TestBuildDistribution:
    def test_empty(self) -> None:
        assert build_distribution([], 10) == []

    def test_single_bucket(self) -> None:
        values = [45.0, 48.0, 42.0]  # All in 40-50 bucket
        dist = build_distribution(values, 10)
        assert len(dist) == 1
        assert dist[0] == [40, 50, 3]

    def test_multiple_buckets(self) -> None:
        values = [25.0, 35.0, 45.0, 55.0, 65.0]
        dist = build_distribution(values, 10)

        # Should have buckets for 20-30, 30-40, 40-50, 50-60, 60-70
        assert len(dist) == 5
        assert dist[0] == [20, 30, 1]
        assert dist[4] == [60, 70, 1]

    def test_bucket_boundaries(self) -> None:
        values = [30.0, 30.0, 30.0]  # Exactly on boundary
        dist = build_distribution(values, 10)
        assert len(dist) == 1
        assert dist[0] == [30, 40, 3]

    def test_sparse_buckets(self) -> None:
        values = [10.0, 50.0]  # Gap in middle
        dist = build_distribution(values, 10)

        # Only buckets with counts > 0 are included
        assert len(dist) == 2
        bucket_starts = [d[0] for d in dist]
        assert 10 in bucket_starts
        assert 50 in bucket_starts


class TestBuildDistributions:
    def test_all_distributions(self) -> None:
        dives = [
            make_dive(depth=50, duration=2400, temp_low=55),
            make_dive(depth=80, duration=3000, temp_low=48),
        ]
        dists = build_distributions(dives)

        assert 'depth' in dists
        assert 'duration' in dists
        assert 'temperature' in dists

        # Depth: 50 and 80 -> buckets at 50-60 and 80-90
        depth_starts = [d[0] for d in dists['depth']]
        assert 50 in depth_starts
        assert 80 in depth_starts

        # Temperature: 55 and 48 -> buckets at 50-60 and 40-50
        temp_starts = [d[0] for d in dists['temperature']]
        assert 50 in temp_starts
        assert 40 in temp_starts


class TestBuildLocationStats:
    def test_empty(self) -> None:
        assert build_location_stats([]) == {}

    def test_single_region(self) -> None:
        # Use a real site name from the locations config (Washington)
        dives = [
            make_dive(site='Fort Ward', depth=60, temp_low=52),
            make_dive(site='Rockaway', depth=80, temp_low=50),
        ]
        stats = build_location_stats(dives)

        assert 'Washington' in stats
        assert stats['Washington']['dives'] == 2
        assert stats['Washington']['avg_depth'] == 70
        assert stats['Washington']['avg_temp'] == 51

    def test_multiple_regions(self) -> None:
        dives = [
            make_dive(site='Fort Ward', depth=60, temp_low=52),
            make_dive(site='Darwin', depth=100, temp_low=78),
        ]
        stats = build_location_stats(dives)

        assert 'Washington' in stats
        assert 'Galapagos' in stats
        assert stats['Washington']['dives'] == 1
        assert stats['Galapagos']['dives'] == 1

    def test_numbered_dive_sites(self) -> None:
        """Dive sites with number prefixes should match regions."""
        dives = [
            make_dive(
                depth=60,
                temp_low=52,
                directory='2023-01-01 1 Sund Rock South Wall',
            ),
            make_dive(
                depth=70,
                temp_low=50,
                directory='2023-01-01 2 Sund Rock North Wall',
            ),
        ]
        stats = build_location_stats(dives)

        assert 'Washington' in stats
        assert stats['Washington']['dives'] == 2


class TestBuildTotals:
    def test_empty(self) -> None:
        totals = build_totals([])
        assert totals['logged_dives'] == 0
        assert totals['total_bottom_time_hours'] == 0.0
        assert totals['unique_sites'] == 0

    def test_with_dives(self) -> None:
        dives = [
            make_dive(depth=50, duration=3600, directory='2023-01-01 Site A'),
            make_dive(depth=100, duration=3600, directory='2023-01-02 Site B'),
            make_dive(depth=75, duration=3600, directory='2023-01-03 Site A'),
        ]
        totals = build_totals(dives)

        assert totals['logged_dives'] == 3
        assert totals['total_bottom_time_hours'] == 3.0
        assert totals['unique_sites'] == 2
