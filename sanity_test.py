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

    g_scientific = taxonomy.mapping()
    t_scientific = {v.replace(' sp', ''): k for k, v in g_scientific.items()}

    def test_html_title(self):
        ''' html titles ordering
        '''
        samples = [
            (
                # gallery simple case
                'gallery',
                ['chiton'],
                ['chiton.html', 'buffer', 'gallery/index.html'],
            ),
            (
                # gallery multi level
                'gallery',
                ['brittle', 'star'],
                ['brittle-star.html', 'buffer', 'gallery/index.html'],
            ),
            (
                # gallery, has scientific name
                'gallery',
                ['giant pacific', 'octopus'],
                [
                    'giant-pacific.html',
                    'octopus.html',
                    'buffer',
                    'gallery/index.html',
                    (
                        'Animalia-Mollusca-Cephalopoda-Octopoda-Octopodoidea-'
                        'Enteroctopodidae-Enteroctopus-dofleini.html'
                    ),
                ],
            ),
            (
                # taxonomy, simple case
                'taxonomy',
                ['Animalia'],
                ['taxonomy/index.html', 'buffer', 'Animalia.html'],
            ),
            (
                # taxonomy, no common name
                'taxonomy',
                ['Animalia', 'Echinodermata'],
                [
                    'taxonomy/index.html',
                    'buffer',
                    'Animalia.html',
                    'Animalia-Echinodermata.html',
                ],
            ),
            (
                # taxonomy, has common name
                'taxonomy',
                [
                    'Animalia',
                    'Mollusca',
                    'Cephalopoda',
                    'Octopoda',
                    'Octopodoidea',
                    'Enteroctopodidae',
                    'Enteroctopus',
                    'dofleini',
                ],
                [
                    'taxonomy/index.html',
                    'buffer',
                    'Animalia.html',
                    'Animalia-Mollusca.html',
                    # a ton more stuff
                    'giant-pacific-octopus.html',
                ],
            ),
        ]
        for where, lineage, elements in samples:

            if where == 'gallery':
                scientific = TestGallery.g_scientific
            else:
                scientific = TestGallery.t_scientific

            html, title = gallery.html_title(lineage, where, scientific)

            indices = [html.find(e) for e in elements]
            self.assertEqual(indices, sorted(indices), lineage)
            self.assertEqual(title, ' '.join(lineage))

    def test_html_title_top(self):
        ''' html titles top level
        '''
        # gallery
        html, title = gallery.html_title(
            [], 'gallery', TestGallery.g_scientific
        )
        self.assertEqual(title, 'Diving Gallery')
        self.assertIn('<title>Diving Gallery</title>', html)

        # taxonomy
        html, title = gallery.html_title(
            [], 'taxonomy', TestGallery.t_scientific
        )
        self.assertEqual(title, 'Diving Taxonomy')
        self.assertIn('<title>Diving Taxonomy</title>', html)

    def test_find_representative(self):
        ''' picking the newest image to represent a tree, or a predefined
        'pinned' image
        '''
        tree = collection.go()

        self.assertIn('fish', tree)
        out = gallery.find_representative(tree['fish'], lineage=['fish'])
        self.assertEqual(out.name, 'Juvenile Yellow Eye Rockfish')

        self.assertIn('barnacle', tree)
        out = gallery.find_representative(
            tree['barnacle'], lineage=['barnacle']
        )
        self.assertIsNotNone(out)

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
            match = gallery.gallery_scientific(
                lineage, TestGallery.g_scientific
            )
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
