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

    def test_where_to_words(self) -> None:
        '''control splitting for sites so we don't end up with 'Fort', etc'''
        samples = [
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
