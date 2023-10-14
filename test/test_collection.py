import unittest

from util import collection, image


class TestCollection(unittest.TestCase):
    '''collection.py'''

    def test_expand_names(self) -> None:
        '''it works'''
        base = image.Image("001 - Fish and Coral.jpg", "2021-11-05 10 Rockaway Beach")
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 2)
        fish = out[0]
        coral = out[1]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(coral.name, 'Coral')
        self.assertEqual(fish.number, coral.number)
        self.assertEqual(fish.directory, coral.directory)

    def test_expand_names_noop(self) -> None:
        '''it works'''
        base = image.Image("001 - Fish", "2021-11-05 10 Rockaway Beach")
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 1)
        fish = out[0]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(fish.number, '001')


if __name__ == '__main__':
    unittest.main()
