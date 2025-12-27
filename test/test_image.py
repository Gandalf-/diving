import unittest

from diving.util import database, image


class TestImage(unittest.TestCase):
    """image.py"""

    def setUp(self) -> None:
        database.use_test_database()

    def test_egg_reorder(self) -> None:
        """reinterpret fish eggs as eggs fish"""
        img = image.Image('001 - Fish Eggs.jpg', '2020-01-01 Rockaway Beach')
        self.assertEqual(img.name, 'Eggs Fish')

    def test_categorize(self) -> None:
        """subjects are recategorized, but that needs to be undone for some
        presentations
        """
        samples = [
            ('prawn', 'prawn shrimp'),
            ('french grunt', 'french grunt fish'),
            ('kelp greenling', 'kelp greenling fish'),
            ('giant pacific octopus', 'giant pacific octopus'),
            ('noble sea lemon', 'noble sea lemon nudibranch'),
            ('brain coral', 'brain coral'),
        ]
        for before, after in samples:
            self.assertEqual(image.categorize(before), after)
            self.assertEqual(before, image.uncategorize(after))

    def test_unqualify(self) -> None:
        """remove qualifiers"""
        samples = [
            ('adult male kelp greenling', 'kelp greenling'),
            ('giant pacific octopus', 'giant pacific octopus'),
        ]
        for before, after in samples:
            self.assertEqual(image.unqualify(before), after)

    def test_split(self) -> None:
        """some names are broken to categorize them"""
        samples = [
            ('copper rockfish', 'copper rock fish'),
            ('eagleray', 'eagle ray'),
            ('six rayed star', 'six rayed star'),
            ('giant pacific octopus', 'giant pacific octopus'),
        ]
        for before, after in samples:
            split = image.split(before)
            self.assertEqual(split, after)
            self.assertEqual(image.unsplit(split), before)

    def test_image_location(self) -> None:
        """names can have a number after the date to force ordering that
        should be removed usually
        """
        samples = [
            ('2021-11-05 Rockaway Beach', '2021-11-05 Rockaway Beach'),
            ('2021-11-05 1 Rockaway Beach', '2021-11-05 Rockaway Beach'),
            ('2021-11-05 10 Rockaway Beach', '2021-11-05 Rockaway Beach'),
        ]
        for before, after in samples:
            picture = image.Image('fish', before)
            self.assertEqual(picture.location(), after)

    def test_image_site(self) -> None:
        """it works"""
        samples = [
            ('2021-11-05 Rockaway Beach', 'Rockaway Beach'),
            ('2021-11-05 1 Rockaway Beach', 'Rockaway Beach'),
            ('2021-11-05 10 Rockaway Beach', 'Rockaway Beach'),
        ]
        for before, after in samples:
            picture = image.Image('fish', before)
            self.assertEqual(picture.site(), after)

    def test_image_singular(self) -> None:
        """it works"""
        samples = [
            ('001 - Sea Lemon.jpg', 'sea lemon'),
            ('001 - Clams.jpg', 'clam'),
            ('001 - Decorator Crabs.jpg', 'decorator crab'),
            ('001 - Green Algae.jpg', 'green algae'),
            ('001 - Octopus.jpg', 'octopus'),
            ('001 - Grass.jpg', 'grass'),
            ('001 - Painted Chitons.jpg', 'painted chiton'),
        ]
        for before, after in samples:
            picture = image.Image(before, '2020-01-01 Rockaway Beach')
            self.assertEqual(picture.singular(), after)

    def test_image_simplified(self) -> None:
        """it works"""
        samples = [
            ('001 - Clams.jpg', 'clam'),
            ('001 - Juvenile Decorator Crab.jpg', 'decorator crab'),
            ('001 - Green Algae.jpg', 'green algae'),
            ('001 - Octopus Eggs.jpg', 'eggs octopus'),
            ('001 - Various Grass.jpg', 'grass'),
            ('001 - Painted Chitons.jpg', 'painted chiton'),
            ('001 - Kelp Greenling Eggs.jpg', 'eggs kelp greenling'),
        ]
        for before, after in samples:
            picture = image.Image(before, '2020-01-01 Rockaway Beach')
            self.assertEqual(picture.simplified(), after)

    def test_image_basics(self) -> None:
        img = image.Image('001 - Clams.jpg', '2020-01-01 Rockaway Beach')
        self.assertEqual(img.name, 'Clams')
        self.assertEqual(img.number, '001')
        self.assertEqual(img.directory, '2020-01-01 Rockaway Beach')
        self.assertTrue(img.is_image)
        self.assertFalse(img.is_video)

        self.assertEqual(img.thumbnail(), '/imgs/test.webp')
        self.assertEqual(img.fullsize(), '/full/test.webp')

    def test_video_basics(self) -> None:
        img = image.Image('001 - Clams.mov', '2020-01-01 Rockaway Beach')
        self.assertEqual(img.name, 'Clams')
        self.assertEqual(img.number, '001')
        self.assertEqual(img.directory, '2020-01-01 Rockaway Beach')
        self.assertFalse(img.is_image)
        self.assertTrue(img.is_video)

        self.assertEqual(img.thumbnail(), '/clips/test.mp4')
        self.assertEqual(img.fullsize(), '/video/test.mp4')

    def test_has_multiple_subjects(self) -> None:
        """check if image name contains multiple subjects"""
        from diving.util.collection import expand_names

        samples = [
            ('001 - Shark and Remora.jpg', True),
            ('001 - Crab with Anemone.jpg', True),
            ('001 - Fish and Kelp.jpg', True),
            ('001 - Giant Pacific Octopus.jpg', False),
            ('001 - Painted Chiton.jpg', False),
            ('001.jpg', False),
        ]
        for label, expected in samples:
            img = image.Image(label, '2020-01-01 Rockaway Beach')
            self.assertEqual(img.has_multiple_subjects(), expected, f'Failed for {label}')

            # Also test after expand_names processes it
            expanded = list(expand_names([img]))
            for expanded_img in expanded:
                self.assertEqual(
                    expanded_img.has_multiple_subjects(),
                    expected,
                    f'Failed for {label} after expand_names',
                )

    def test_depth_at_beyond_range(self) -> None:
        """_depth_at should handle position beyond all depth measurements"""
        depths = [(0.0, 0), (0.5, 30), (0.8, 50)]

        # Position beyond all measurements should return last depth (50)
        result = image._depth_at(depths, 1.0)
        self.assertEqual(result, 50)

        # Also test with position slightly beyond
        result = image._depth_at(depths, 0.95)
        self.assertEqual(result, 50)
