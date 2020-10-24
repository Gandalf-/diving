'''
Sanity checks
'''

import unittest

import collection
import taxonomy
import gallery
import image


class TestGallery(unittest.TestCase):
    ''' gallery.py '''

    scientific = taxonomy.mapping()
    # tree = collection.go()

    def test_lineage_to_link(self):
        ''' converting lineage to links between sites
        '''
        samples = [
                (None, False, ["a", "b", "c"], "a-b-c"),
                (None, True, ["a", "b", "c"], "a-b-c"),
                ("d", False, ["a", "b", "c"], "d-a-b-c"),
                ("d", True, ["a", "b", "c"], "a-b-c-d"),
        ]
        for key, right_side, lineage, after in samples:
            side = 'right' if right_side else 'left'
            link = gallery.lineage_to_link(lineage, side, key)
            self.assertEqual(link, after)

    def test_gallery_scientific(self):
        ''' find scientific names by common name
        '''
        samples = [
            (['copper', 'rock', 'fish'], 'Sebastes caurinus'),
            (['fish'], 'Actinopterygii sp'),
            (['fish', 'eggs'], 'Actinopterygii sp'),
            (['juvenile yellow eye', 'rock', 'fish'], 'Sebastes ruberrimus'),
        ]

        for lineage, output in samples:
            match = gallery.gallery_scientific(lineage, TestGallery.scientific)
            self.assertTrue(match.endswith(output), match)


class TestImage(unittest.TestCase):
    ''' image.py '''

    def test_categorize(self):
        ''' subjects are recategorized, but that needs to be undone for some
        presentations
        '''
        samples = [
                ("prawn", "prawn shrimp"),
                ("french grunt", "french grunt fish"),
                ("kelp greenling", "kelp greenling fish"),
                ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            self.assertEqual(image.categorize(before), after)
            self.assertEqual(before, image.uncategorize(after))

    def test_unqualify(self):
        ''' remove qualifiers '''
        samples = [
                ("juvenile red octopus egg", "red octopus"),
                ("dead male kelp greenling", "kelp greenling"),
                ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            self.assertEqual(image.unqualify(before), after)

    def test_split(self):
        ''' some names are broken to categorize them '''
        samples = [
                ("copper rockfish", "copper rock fish"),
                ("eagleray", "eagle ray"),
                ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            split = image.split(before)
            self.assertEqual(split, after)
            self.assertEqual(image.unsplit(split), before)


if __name__ == '__main__':
    unittest.main()
