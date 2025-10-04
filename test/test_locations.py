import unittest

import locations


class TestLocations(unittest.TestCase):
    """locations.py"""

    def test_site_list(self) -> None:
        """site_list"""
        self.assertEqual(
            locations.site_list(),
            'Bonaire, British Columbia, Curacao, Galapagos, Maldives, Roatan, and Washington',
        )

    def test_get_region(self) -> None:
        samples = [
            ('Edmonds', 'Washington'),
            ('Oil Slick', 'Bonaire'),
            ('Klein M', 'Bonaire'),
            ('Rockaway Stretch Reef', 'Washington'),
            ('Aquarium', 'British Columbia'),
            ('Agnew', 'British Columbia'),
            ('Captain Island Light', 'British Columbia'),
        ]
        for site, context in samples:
            self.assertEqual(locations.get_region(site), context)

    def test_get_subregion(self) -> None:
        samples = [
            ('Edmonds', None),
            ('Oil Slick', None),
            ('Aquarium', 'Queen Charlotte Strait'),
            ('Agnew', 'Jervis Inlet'),
            ('Captain Island Light', 'Jervis Inlet'),
        ]
        for site, subregion in samples:
            self.assertEqual(locations.get_subregion(site), subregion)

    def test_add_context(self) -> None:
        """add_context"""
        samples = [
            ('Edmonds', 'Washington Edmonds'),
            ('Oil Slick', 'Bonaire Oil Slick'),
            ('Klein M', 'Bonaire Klein M'),
            ('Rockaway Stretch Reef', 'Washington Rockaway Stretch Reef'),
            ('Aquarium', 'British Columbia Queen Charlotte Strait Aquarium'),
            ('Agnew', 'British Columbia Jervis Inlet Agnew'),
            ('Captain Island Light', 'British Columbia Jervis Inlet Captain Island Light'),
        ]
        for before, after in samples:
            self.assertEqual(locations.add_context(before), after)

    def test_where_to_words(self) -> None:
        """control splitting for sites so we don't end up with 'Fort', etc"""
        samples = [
            ('British Columbia', ['British Columbia']),
            (
                'British Columbia Jervis Inlet Argonaut Point',
                ['British Columbia', 'Jervis Inlet', 'Argonaut Point'],
            ),
            (
                'British Columbia Queen Charlotte Strait Aquarium',
                ['British Columbia', 'Queen Charlotte Strait', 'Aquarium'],
            ),
            ('Washington Edmonds', ['Washington', 'Edmonds']),
            ('Washington Fort Ward', ['Washington', 'Fort Ward']),
            (
                'Washington Sund Rock South Wall',
                ['Washington', 'Sund Rock', 'South', 'Wall'],
            ),
        ]
        for before, after in samples:
            self.assertEqual(locations.where_to_words(before), after)

    def test_region_year_ranges(self) -> None:
        ranges = locations._region_year_ranges()

        self.assertEqual(ranges['Galapagos'], {2021})
        self.assertEqual(ranges['Maldives'], {2022})
        self.assertEqual(ranges['British Columbia'], {2020, 2022, 2023, 2024, 2025})

        self.assertEqual(ranges['Bonaire Cliff'], {2019})
        self.assertEqual(ranges['British Columbia Jervis Inlet'], {2020, 2022, 2023, 2025})
        self.assertEqual(ranges['British Columbia Queen Charlotte Strait'], {2023, 2024})
        self.assertEqual(ranges['British Columbia Jervis Inlet Agnew'], {2023, 2025})
        self.assertEqual(ranges['British Columbia Queen Charlotte Strait Aquarium'], {2023, 2024})
        self.assertEqual(ranges['Galapagos Fernandina'], {2021})

    def test_pretty_year_range(self) -> None:
        self.assertEqual(locations._pretty_year_range({1, 3, 4, 6}), '1, 3-4, 6')
        self.assertEqual(locations._pretty_year_range({1, 2, 3, 4, 5, 6}), '1-6')
        self.assertEqual(locations._pretty_year_range({1, 6}), '1, 6')

    def test_region_to_year_range(self) -> None:
        self.assertEqual(locations.find_year_range(['Galapagos']), '2021')
        self.assertEqual(locations.find_year_range(['Galapagos']), '2021')
        self.assertEqual(locations.find_year_range(['Maldives']), '2022')
        self.assertEqual(locations.find_year_range(['British Columbia']), '2020, 2022-2025')

        self.assertEqual(
            locations.find_year_range(['British Columbia', 'Jervis Inlet']),
            '2020, 2022-2023, 2025',
        )
        self.assertEqual(
            locations.find_year_range(['British Columbia', 'Queen Charlotte Strait']),
            '2023-2024',
        )
        self.assertEqual(
            locations.find_year_range(['British Columbia', 'Jervis Inlet', 'Agnew']),
            '2023, 2025',
        )
        self.assertEqual(
            locations.find_year_range(['British Columbia', 'Queen Charlotte Strait', 'Aquarium']),
            '2023-2024',
        )
        self.assertEqual(
            locations.find_year_range(['Galapagos', 'Wolf', 'Shark Bay']),
            '2021',
        )
        self.assertEqual(
            locations.find_year_range(['Galapagos', 'Fernandina']),
            '2021',
        )


if __name__ == '__main__':
    unittest.main()
