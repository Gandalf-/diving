import unittest

from util import image


class TestImage(unittest.TestCase):
    '''image.py'''

    def test_categorize(self) -> None:
        '''subjects are recategorized, but that needs to be undone for some
        presentations
        '''
        samples = [
            ("prawn", "prawn shrimp"),
            ("french grunt", "french grunt fish"),
            ("kelp greenling", "kelp greenling fish"),
            ("giant pacific octopus", "giant pacific octopus"),
            ("noble sea lemon", "noble sea lemon nudibranch"),
            ('brain coral', 'brain coral'),
        ]
        for before, after in samples:
            self.assertEqual(image.categorize(before), after)
            self.assertEqual(before, image.uncategorize(after))

    def test_unqualify(self) -> None:
        '''remove qualifiers'''
        samples = [
            ("juvenile red octopus egg", "red octopus"),
            ("dead male kelp greenling", "kelp greenling"),
            ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            self.assertEqual(image.unqualify(before), after)

    def test_split(self) -> None:
        '''some names are broken to categorize them'''
        samples = [
            ("copper rockfish", "copper rock fish"),
            ("eagleray", "eagle ray"),
            ("six rayed star", "six rayed star"),
            ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            split = image.split(before)
            self.assertEqual(split, after)
            self.assertEqual(image.unsplit(split), before)

    def test_image_location(self) -> None:
        '''names can have a number after the date to force ordering that
        should be removed usually
        '''
        samples = [
            ("2021-11-05 Rockaway Beach", "2021-11-05 Rockaway Beach"),
            ("2021-11-05 1 Rockaway Beach", "2021-11-05 Rockaway Beach"),
            ("2021-11-05 10 Rockaway Beach", "2021-11-05 Rockaway Beach"),
        ]
        for before, after in samples:
            picture = image.Image('fish', before)
            self.assertEqual(picture.location(), after)

    def test_image_site(self) -> None:
        '''it works'''
        samples = [
            ("2021-11-05 Rockaway Beach", "Rockaway Beach"),
            ("2021-11-05 1 Rockaway Beach", "Rockaway Beach"),
            ("2021-11-05 10 Rockaway Beach", "Rockaway Beach"),
        ]
        for before, after in samples:
            picture = image.Image('fish', before)
            self.assertEqual(picture.site(), after)

    def test_image_singular(self) -> None:
        '''it works'''
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
        '''it works'''
        samples = [
            ('001 - Clams.jpg', 'clam'),
            ('001 - Juvenile Decorator Crab Eggs.jpg', 'decorator crab'),
            ('001 - Green Algae.jpg', 'green algae'),
            ('001 - Octopus Egg.jpg', 'octopus'),
            ('001 - Various Grass.jpg', 'grass'),
            ('001 - Painted Chitons.jpg', 'painted chiton'),
        ]
        for before, after in samples:
            picture = image.Image(before, '2020-01-01 Rockaway Beach')
            self.assertEqual(picture.simplified(), after)
