import unittest

import locations


class TestLocations(unittest.TestCase):
    '''locations.py'''

    def test_site_list(self) -> None:
        '''site_list'''
        self.assertEqual(
            locations.site_list(),
            'Bonaire, British Columbia, Galapagos, Maldives, and Washington',
        )

    def test_add_context(self) -> None:
        '''add_context'''
        samples = [
            ('Edmonds', 'Washington Edmonds'),
            ('Bonaire Oil Slick', 'Bonaire Oil Slick'),
            ('Klein Bonaire M', 'Bonaire Klein Bonaire M'),
            ('Rockaway Stretch Reef', 'Washington Rockaway Stretch Reef'),
        ]
        for before, after in samples:
            self.assertEqual(locations.add_context(before), after)


if __name__ == '__main__':
    unittest.main()
