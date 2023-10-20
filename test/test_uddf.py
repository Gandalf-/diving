import os
import unittest
from datetime import datetime

from util import collection, common
from util.uddf import (
    _build_dive_history,
    _load_dive_info,
    _match_dive_info,
    _parse,
    search,
    series_match,
)


class TestUDDF(unittest.TestCase):
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
        self.assertEqual(expected, _parse(fname))

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
        self.assertEqual(expected, _parse(fname))

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
        self.assertEqual(expected, _parse(fname))

    def test_parse_sml(self) -> None:
        fname = '99809020-2021-01-09T10_39_00-0.sml'
        expected = {
            'date': datetime.fromisoformat('2021-01-09T10:39:00'),
            'number': 23,
            'depth': 93,
            'duration': 3620,
            'tank_start': 3190,
            'tank_end': 928,
            'temp_high': 46,
            'temp_low': 44,
        }
        self.assertEqual(expected, _parse(fname))

    def test_load(self) -> None:
        dives = list(_load_dive_info())
        self.assertGreater(len(dives), 0)

        numbers = sorted([d['number'] for d in dives])
        self.assertIn(370, numbers)

        # too short
        self.assertNotIn(243, numbers)

    def test_build_history(self) -> None:
        history = _build_dive_history()
        self.assertEqual(history['2023-09-24'], ['1 Power Lines', '2 Jaggy Crack'])
        self.assertEqual(history['2023-09-10'], ['Rockaway Beach'])
        self.assertNotIn('5 Ari South Maihi Beyru', history['2022-11-10'])

    def test_match_single(self) -> None:
        fname = 'Perdix AI[385834A0]#161_2023-09-10.uddf'
        dive = next(_match_dive_info(_parse(f) for f in [fname]))
        self.assertEqual(dive['site'], 'Rockaway Beach')
        self.assertEqual(dive['directory'], '2023-09-10 Rockaway Beach')

    def test_match_double(self) -> None:
        f169 = 'Perdix AI[385834A0]#169_2023-09-24.uddf'
        f170 = 'Perdix AI[385834A0]#170_2023-09-24.uddf'
        e169, e170 = list(_match_dive_info(_parse(f) for f in [f169, f170]))

        self.assertEqual(e169['site'], '1 Power Lines')
        self.assertEqual(e169['directory'], '2023-09-24 1 Power Lines')
        self.assertEqual(e170['site'], '2 Jaggy Crack')
        self.assertEqual(e170['directory'], '2023-09-24 2 Jaggy Crack')

    def test_match_triple(self) -> None:
        f134 = 'Perdix AI[385834A0]#134_2023-04-04.uddf'
        f135 = 'Perdix AI[385834A0]#135_2023-04-04.uddf'
        f136 = 'Perdix AI[385834A0]#136_2023-04-04.uddf'
        e134, e135, e136 = list(_match_dive_info(_parse(f) for f in [f134, f135, f136]))

        self.assertEqual(e134['site'], '1 Fantasy Island')
        self.assertEqual(e135['site'], '2 Hussar Bay')
        self.assertEqual(e136['site'], '3 Browning Wall')

    def test_integration(self) -> None:
        dives = common.take(_match_dive_info(_load_dive_info()), 100)
        self.assertEqual(len(dives), 100)
        directories = set(os.path.basename(d) for d in collection.dive_listing())

        for dive in dives:
            self.assertGreater(dive['number'], 0)
            self.assertGreater(dive['depth'], 10)
            self.assertGreater(dive['duration'], 900)
            self.assertIn('site', dive)
            self.assertIn(dive['directory'], directories)

    def test_maldives(self) -> None:
        f120 = 'Perdix AI[385834A0]#120_2022-11-11.uddf'
        f119 = 'Perdix AI[385834A0]#119_2022-11-11.uddf'
        f102 = 'Perdix AI[385834A0]#102_2022-11-06.uddf'
        e102, e119, e120 = list(_match_dive_info(_parse(f) for f in [f102, f119, f120]))

        self.assertEqual(e102['site'], '1 Male North Kurumba')
        self.assertEqual(e119['site'], '1 Male South Kuda Giri Wreck')
        self.assertEqual(e120['site'], '2 Male North Manta Point')

    '''
    SitesTitle doesn't have exact information on which directory it
    represents and can represent multiple dives if they occurred on
    the same day, so it needs some help
    '''

    def test_search_failure(self) -> None:
        self.assertIsNone(search('2000-01-01', 'Rockaway Beach'))

    def test_search_single(self) -> None:
        self.assertIsNotNone(search('2022-12-03', 'Fort Ward'))

    def test_search_multi_unique(self) -> None:
        info = search('2023-03-11', 'Elephant Wall')
        assert info
        self.assertEqual(info['directory'], '2023-03-11 2 Elephant Wall')

        info = search('2023-04-03', 'Seven Trees')
        assert info
        self.assertEqual(info['directory'], '2023-04-03 2 Seven Trees')

    def test_search_multi_duplicate(self) -> None:
        info = search('2023-09-04', 'Keystone Jetty')
        assert info
        self.assertEqual(info['directory'], '2023-09-04 1 Keystone Jetty')

    def test_series_match(self) -> None:
        series = list(range(0, 100))
        others = list(range(0, 10))

        self.assertEqual(series_match(series, others, 0), 0)
        self.assertEqual(series_match(series, others, 1), 10)
        self.assertEqual(series_match(series, others, 5), 50)
        self.assertEqual(series_match(series, others, 9), 90)

    def test_series_match_non_contiguous(self) -> None:
        series = [1, 2, 3, 4, 5, 15, 16, 17, 18]
        others = [5, 6, 7]

        self.assertEqual(series_match(series, others, 5), 1)
        self.assertEqual(series_match(series, others, 6), 4)
        self.assertEqual(series_match(series, others, 7), 16)
