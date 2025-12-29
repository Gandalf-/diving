import os
from datetime import UTC, datetime

from diving.util import collection, common
from diving.util.log import (
    _build_dive_history,
    _db_decode,
    _db_encode,
    _load_dive_info,
    _match_dive_info,
    _parse,
    search,
    suunto_counter,
)


class TestUDDF:
    def test_db_encode(self) -> None:
        info = {
            'date': datetime.now(UTC),
            'number': 243,
            'depth': 11,
            'duration': 584,
            'tank_start': 2212,
            'tank_end': 1994,
            'temp_high': 78,
            'temp_low': 78,
        }
        assert info == _db_decode(_db_encode(info))
        assert {} == _db_encode({})
        assert {} == _db_decode({})

    def test_parse_uddf_short(self) -> None:
        fname = 'Perdix AI[385834A0]#43_2021-10-22.uddf'
        expected = {
            'date': datetime.fromisoformat('2021-10-22T20:24:03Z'),
            'number': 243,
            'depth': 11,
            'duration': 584,
            'tank_start': 2212,
            'tank_end': 1994,
            'temp_high': 78,
            'temp_low': 78,
        }
        parsed = _parse(fname)
        for key, value in expected.items():
            assert parsed[key] == value, f'{key}: {parsed[key]} != {value}'
        assert parsed['depths'] != ()

    def test_parse_uddf_long(self) -> None:
        fname = 'Perdix AI[385834A0]#169_2023-09-24.uddf'
        expected = {
            'date': datetime.fromisoformat('2023-09-24T09:26:24Z'),
            'number': 369,
            'depth': 140,
            'duration': 2564,
            'tank_start': 2978,
            'tank_end': 740,
            'temp_high': 59,
            'temp_low': 46,
        }
        parsed = _parse(fname)
        for key, value in expected.items():
            assert parsed[key] == value, f'{key}: {parsed[key]} != {value}'
        assert parsed['depths'] != ()

    def test_parse_uddf_zero_start_pressure(self) -> None:
        fname = 'Perdix AI[385834A0]#165_2023-09-22.uddf'
        expected = {
            'date': datetime.fromisoformat('2023-09-22T15:20:14Z'),
            'number': 365,
            'depth': 84,
            'duration': 2823,
            'tank_start': 3500,
            'tank_end': 1120,
            'temp_high': 59,
            'temp_low': 48,
        }
        parsed = _parse(fname)
        for key, value in expected.items():
            assert parsed[key] == value, f'{key}: {parsed[key]} != {value}'
        assert parsed['depths'] != ()

    def test_parse_sml(self) -> None:
        # Reset counter so test doesn't depend on execution order
        suunto_counter.value = 21
        fname = '99809020-2021-01-09T10_39_00-0.sml'
        expected = {
            'date': datetime.fromisoformat('2021-01-09T10:39:00'),
            'number': 22,
            'depth': 93,
            'depths': (),  # frozen, so tuple not list
            'duration': 3620,
            'tank_start': 3190,
            'tank_end': 928,
            'temp_high': 46,
            'temp_low': 44,
        }
        parsed = _parse(fname)
        for key, value in expected.items():
            assert parsed[key] == value, f'{key}: {parsed[key]} != {value}'

    def test_load(self) -> None:
        dives = list(_load_dive_info())
        assert len(dives) > 0

        numbers = sorted([d['number'] for d in dives])
        assert 370 in numbers

        # too short
        assert 243 not in numbers

    def test_build_history(self) -> None:
        history = _build_dive_history()
        assert history['2023-09-24'] == ['1 Power Lines', '2 Jaggy Crack']
        assert history['2023-09-10'] == ['Rockaway Beach']
        assert '5 Ari South Maihi Beyru' not in history['2022-11-10']

    def test_match_single(self) -> None:
        fname = 'Perdix AI[385834A0]#161_2023-09-10.uddf'
        dive = next(_match_dive_info(_parse(f) for f in [fname]))
        assert dive['site'] == 'Rockaway Beach'
        assert dive['directory'] == '2023-09-10 Rockaway Beach'

    def test_match_double(self) -> None:
        f169 = 'Perdix AI[385834A0]#169_2023-09-24.uddf'
        f170 = 'Perdix AI[385834A0]#170_2023-09-24.uddf'
        e169, e170 = list(_match_dive_info(_parse(f) for f in [f169, f170]))

        assert e169['site'] == '1 Power Lines'
        assert e169['directory'] == '2023-09-24 1 Power Lines'
        assert e170['site'] == '2 Jaggy Crack'
        assert e170['directory'] == '2023-09-24 2 Jaggy Crack'

    def test_match_triple(self) -> None:
        f134 = 'Perdix AI[385834A0]#134_2023-04-04.uddf'
        f135 = 'Perdix AI[385834A0]#135_2023-04-04.uddf'
        f136 = 'Perdix AI[385834A0]#136_2023-04-04.uddf'
        e134, e135, e136 = list(_match_dive_info(_parse(f) for f in [f134, f135, f136]))

        assert e134['site'] == '1 Fantasy Island'
        assert e135['site'] == '2 Hussar Bay'
        assert e136['site'] == '3 Browning Wall'

    def test_integration(self) -> None:
        dives = common.take(_match_dive_info(_load_dive_info()), 100)
        assert len(dives) == 100
        directories = set(os.path.basename(d) for d in collection.dive_listing())

        for dive in dives:
            assert dive['number'] > 0
            assert dive['depth'] > 10
            assert dive['duration'] > 900
            assert 'site' in dive
            assert dive['directory'] in directories

    def test_maldives(self) -> None:
        f120 = 'Perdix AI[385834A0]#120_2022-11-11.uddf'
        f119 = 'Perdix AI[385834A0]#119_2022-11-11.uddf'
        f102 = 'Perdix AI[385834A0]#102_2022-11-06.uddf'
        e102, e119, e120 = list(_match_dive_info(_parse(f) for f in [f102, f119, f120]))

        assert e102['site'] == '1 Male North Kurumba'
        assert e119['site'] == '1 Male South Kuda Giri Wreck'
        assert e120['site'] == '2 Male North Manta Point'

    """
    SitesTitle doesn't have exact information on which directory it
    represents and can represent multiple dives if they occurred on
    the same day, so it needs some help
    """

    def test_search_failure(self) -> None:
        assert search('2000-01-01', 'Rockaway Beach') is None

    def test_search_single(self) -> None:
        assert search('2022-12-03', 'Fort Ward') is not None

    def test_search_multi_unique(self) -> None:
        info = search('2023-03-11', 'Elephant Wall')
        assert info
        assert info['directory'] == '2023-03-11 2 Elephant Wall'

        info = search('2023-04-03', 'Seven Tree')
        assert info
        assert info['directory'] == '2023-04-03 2 Seven Tree'

    def test_search_multi_duplicate(self) -> None:
        info = search('2023-09-04', 'Keystone Jetty')
        assert info
        assert info['directory'] == '2023-09-04 1 Keystone Jetty'

    def test_search_bug_skip(self) -> None:
        info = search('2024-10-30', 'Pigeon Key Shallows')
        assert not info, info

    def test_search_bug_cover(self) -> None:
        info = search('2024-10-30', 'Morerat Wall')
        assert info
