import unittest
from datetime import datetime

from util.uddf import load_dive_info, parse, match_dive_info, build_dive_history
from util import common


class TestUDDF(unittest.TestCase):
    def test_parse(self) -> None:
        fname = 'Perdix AI[385834A0]#43_2021-10-22.uddf'
        expected = {
            'date': datetime.fromisoformat('2021-10-22T20:24:03Z'),
            'number': 43,
            'depth': 11,
            'duration': 584,
            'tank_start': 15251209,
            'tank_end': 13858467,
        }
        self.assertEqual(expected, parse(fname))

    def test_load(self) -> None:
        dives = list(load_dive_info())
        self.assertGreater(len(dives), 0)

        # too short
        numbers = sorted([d['number'] for d in dives])
        self.assertIn(170, numbers)
        self.assertNotIn(43, numbers)

    def test_build_history(self) -> None:
        history = build_dive_history()
        self.assertEqual(history['2023-09-24'], ['1 Power Lines', '2 Jaggy Crack'])
        self.assertEqual(history['2023-09-10'], ['Rockaway Beach'])

    def test_match_single(self) -> None:
        fname = 'Perdix AI[385834A0]#161_2023-09-10.uddf'
        dive = next(match_dive_info(parse(f) for f in [fname]))
        self.assertEqual(dive['site'], 'Rockaway Beach')
        self.assertEqual(dive['directory'], '2023-09-10 Rockaway Beach')

    def test_match_double(self) -> None:
        f169 = 'Perdix AI[385834A0]#169_2023-09-24.uddf'
        f170 = 'Perdix AI[385834A0]#170_2023-09-24.uddf'
        e169, e170 = list(match_dive_info(parse(f) for f in [f169, f170]))

        self.assertEqual(e169['site'], '1 Power Lines')
        self.assertEqual(e169['directory'], '2023-09-24 1 Power Lines')
        self.assertEqual(e170['site'], '2 Jaggy Crack')
        self.assertEqual(e170['directory'], '2023-09-24 2 Jaggy Crack')

    def test_match_triple(self) -> None:
        f134 = 'Perdix AI[385834A0]#134_2023-04-04.uddf'
        f135 = 'Perdix AI[385834A0]#135_2023-04-04.uddf'
        f136 = 'Perdix AI[385834A0]#136_2023-04-04.uddf'
        e134, e135, e136 = list(match_dive_info(parse(f) for f in [f134, f135, f136]))

        self.assertEqual(e134['site'], '1 Fantasy Island')
        self.assertEqual(e135['site'], '2 Hussar Bay')
        self.assertEqual(e136['site'], '3 Browning Wall')

    def test_integration(self) -> None:
        dives = common.take(match_dive_info(load_dive_info()), 100)
        self.assertEqual(len(dives), 100)

        for dive in dives:
            self.assertGreater(dive['number'], 0)
            self.assertGreater(dive['depth'], 10)
            self.assertGreater(dive['duration'], 900)
            self.assertIn('site', dive)
