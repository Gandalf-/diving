import os
import unittest

from util import collection, database, image, static


class TestCollection(unittest.TestCase):
    """collection.py"""

    def setUp(self) -> None:
        database.use_test_database()

    def test_expand_names(self) -> None:
        """it works"""
        base = image.Image('001 - Fish and Coral.jpg', '2021-11-05 10 Rockaway Beach')
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 2)
        fish = out[0]
        coral = out[1]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(coral.name, 'Coral')
        self.assertEqual(fish.number, coral.number)
        self.assertEqual(fish.directory, coral.directory)

    def test_expand_names_noop(self) -> None:
        """it works"""
        base = image.Image('001 - Fish', '2021-11-05 10 Rockaway Beach')
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 1)
        fish = out[0]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(fish.number, '001')

    def test_position(self) -> None:
        """it works"""
        path = os.path.join(static.image_root, '2023-10-19 3 Sunscape')
        images = collection.delve(path)
        self.assertEqual(len(images), 9)

        first, *_ = images
        *_, last = images
        self.assertGreaterEqual(first.position, 0.0)
        self.assertLessEqual(last.position, 1.0)

        positions = [i.position for i in images]
        self.assertEqual(positions, sorted(positions))


if __name__ == '__main__':
    unittest.main()
