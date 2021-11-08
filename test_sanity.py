'''
Sanity checks
'''

import unittest

import collection
import taxonomy
import gallery
import hypertext
import image
import utility
import information
import locations

from hypertext import Where, Side
from taxonomy import MappingType


class TestHypertext(unittest.TestCase):
    ''' hypertext.py '''

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
            side = Side.Right if right_side else Side.Left
            link = hypertext.lineage_to_link(lineage, side, key)
            self.assertEqual(link, after)

    def test_title_ordering(self):
        ''' html titles ordering
        '''
        samples = [
            (
                # gallery simple case
                Where.Gallery,
                ['chiton'],
                ['chiton.html', 'buffer', 'gallery/index.html'],
            ),
            (
                # gallery multi level
                Where.Gallery,
                ['brittle', 'star'],
                ['brittle-star.html', 'buffer', 'gallery/index.html'],
            ),
            (
                # gallery, has scientific name
                Where.Gallery,
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
                Where.Taxonomy,
                ['Animalia'],
                ['taxonomy/index.html', 'buffer', 'Animalia.html'],
            ),
            (
                # taxonomy, no common name
                Where.Taxonomy,
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
                Where.Taxonomy,
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

            if where == Where.Gallery:
                scientific = TestGallery.g_scientific
            else:
                scientific = TestGallery.t_scientific

            html, title = hypertext.title(lineage, where, scientific)

            indices = [html.find(e) for e in elements]
            self.assertEqual(indices, sorted(indices), lineage)
            self.assertEqual(title, ' '.join(lineage))

    def test_title_names(self):
        ''' html titles top level
        '''
        # gallery
        html, title = hypertext.title(
            [], Where.Gallery, TestGallery.g_scientific
        )
        self.assertEqual(title, 'Gallery')
        self.assertIn('<title>Gallery</title>', html)

        # taxonomy
        html, title = hypertext.title(
            [], Where.Taxonomy, TestGallery.t_scientific
        )
        self.assertEqual(title, 'Taxonomy')
        self.assertIn('<title>Taxonomy</title>', html)


class TestGallery(unittest.TestCase):
    ''' gallery.py '''

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

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


class TestTaxonomy(unittest.TestCase):
    ''' taxonomy.py '''

    def test_gallery_scientific(self):
        ''' find scientific names by common name
        '''
        samples = [
            (['copper', 'rock', 'fish'], 'Sebastes caurinus'),
            (['fish'], 'Actinopterygii sp'),
            (['fish', 'eggs'], 'Actinopterygii sp'),
            (['juvenile yellow eye', 'rock', 'fish'], 'Sebastes ruberrimus'),
            (['noble', 'sea lemon', 'nudibranch'], 'Peltodoris nobilis'),
            (['brain', 'coral'], 'Scleractinia Mussidae'),
            (['multicolor', 'dendronotid', 'nudibranch'], 'diversicolor'),
            (['six rayed', 'star'], 'hexactis'),
            (['mossy', 'chiton'], 'muscosa'),
        ]

        for lineage, output in samples:
            match = taxonomy.gallery_scientific(
                lineage, TestGallery.g_scientific
            )
            self.assertTrue(match.endswith(output), match)

    def test_similar(self):
        ''' can these be collapsed? '''
        samples = [
            (True, ('Amphinomida', 'Amphinomidae')),
            (True, ('Aphrocallistidae', 'Aphrocallistes')),
            (True, ('Clionaida', 'Clionaidae')),
            (True, ('Membraniporoidea', 'Membraniporidae')),
            (True, ('Strongylocentrotidae', 'Strongylocentrotus')),
            (False, ('Comatulida', 'Antedonidae')),
            (False, ('Toxopneustidae', 'Tripneustes')),
        ]
        for expected, (a, b) in samples:
            self.assertEqual(expected, taxonomy.similar(a, b), [a, b])

    def test_simplify(self):
        ''' remove similar non-ambiguous names '''
        samples = [
            (
                'Polyplacophora Chitonida Mopalioidea Mopaliidae',
                'Polyplacophora Chitonida M. Mopaliidae',
            ),
            (
                'Cheiragonoidea Cheiragonidae Telmessus cheiragonus',
                'C. Cheiragonidae Telmessus cheiragonus',
            ),
            (
                'Diadematoida Diadematidae Diadema antillarum',
                'D. D. Diadema antillarum',
            ),
            (
                'Halcampidae Halcampa decemtentaculata',
                'H. Halcampa decemtentaculata',
            ),
        ]
        for before, after in samples:
            self.assertEqual(after, taxonomy.simplify(before))


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
            ("noble sea lemon", "noble sea lemon nudibranch"),
            ('brain coral', 'brain coral'),
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
            ("six rayed star", "six rayed star"),
            ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            split = image.split(before)
            self.assertEqual(split, after)
            self.assertEqual(image.unsplit(split), before)

    def test_location(self):
        ''' names can have a number after the date to force ordering that
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


class TestUtility(unittest.TestCase):
    ''' utility.py '''

    def test_hmap(self):
        ''' fold-ish thing '''
        out = utility.hmap(0, lambda x: x + 1, lambda x: x * 5)
        self.assertEqual(out, 5)

    def test_tree_size(self):
        ''' how many leaves are in this tree '''
        tree = {'a': {'b': [3, 3]}, 'c': [4, 4, 4]}
        self.assertEqual(utility.tree_size(tree), 5)

    def test_extract_leaves(self):
        ''' grab the leaves for this tree '''
        tree = {'a': {'b': 3}, 'c': 4}
        leaves = list(utility.extract_leaves(tree))
        wanted = [3, 4]
        self.assertEqual(sorted(leaves), sorted(wanted))


class TestInformation(unittest.TestCase):
    ''' information.py '''

    def test_lineage_to_names(self):
        ''' extract the right parts for look up '''
        samples = [
            ([], []),
            (['Animalia'], ['Animalia']),
            (['Animalia', 'Mollusca', 'Gastropoda'], ['Gastropoda']),
            (  # split intermediate stuff
                ['Gastropoda', 'Dendronotoidea Dendronotidae Dendronotus'],
                ['Dendronotoidea', 'Dendronotidae', 'Dendronotus'],
            ),
            (  # genus and species split
                [
                    'Gastropoda',
                    'Dendronotoidea Dendronotidae Dendronotus',
                    'rufus',
                ],
                ['Dendronotus rufus'],
            ),
            (  # genus and species together
                ['Cancroidea Cancridae', 'Glebocarcinus oregonesis'],
                ['Glebocarcinus oregonesis'],
            ),
            (  # genus and species together with extra
                [
                    'Pleurobranchoidea',
                    'Pleurobranchidae Berthella californica',
                ],
                ['Pleurobranchidae', 'Berthella californica'],
            ),
        ]
        for lineage, after in samples:
            parts = information.lineage_to_names(lineage)
            self.assertEqual(parts, after)


class TestLocations(unittest.TestCase):
    ''' locations.py '''

    def test_add_context(self):
        ''' add_context
        '''
        samples = [
            ('Edmonds', 'Washington Edmonds'),
            ('Bonaire Oil Slick', 'Bonaire Oil Slick'),
            ('Klein Bonaire M', 'Bonaire Klein Bonaire M'),
            ('Rockaway Stretch Reef', 'Washington Rockaway Stretch Reef'),
        ]
        for before, after in samples:
            self.assertEqual(locations.add_context(before), after)

    def test_strip_date(self):
        ''' strip_date
        '''


if __name__ == '__main__':
    unittest.main()
