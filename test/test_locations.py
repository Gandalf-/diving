import unittest

import locations


class TestLocations(unittest.TestCase):
    """locations.py"""

    def test_site_list(self) -> None:
        """site_list"""
        self.assertEqual(
            locations.site_list(),
            'Bonaire, British Columbia, Curacao, Galapagos, Maldives, and Washington',
        )

    def test_get_region(self) -> None:
        samples = [
            ('Edmonds', 'Washington'),
            ('Oil Slick', 'Bonaire'),
            ('Klein M', 'Bonaire'),
            ('Rockaway Stretch Reef', 'Washington'),
        ]
        for site, context in samples:
            self.assertEqual(locations.get_region(site), context)

    def test_add_context(self) -> None:
        """add_context"""
        samples = [
            ('Edmonds', 'Washington Edmonds'),
            ('Oil Slick', 'Bonaire Oil Slick'),
            ('Klein M', 'Bonaire Klein M'),
            ('Rockaway Stretch Reef', 'Washington Rockaway Stretch Reef'),
        ]
        for before, after in samples:
            self.assertEqual(locations.add_context(before), after)

    def test_where_to_words(self) -> None:
        """control splitting for sites so we don't end up with 'Fort', etc"""
        samples = [
            ('British Columbia', ['British Columbia']),
            (
                'British Columbia Argonaut Point',
                ['British Columbia', 'Argonaut Point'],
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


if __name__ == '__main__':
    unittest.main()
