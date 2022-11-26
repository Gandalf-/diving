'''
Sanity checks
'''

import copy
import unittest

import gallery
import hypertext
import information
import locations

from util import collection
from util import image
from util import taxonomy
from util import verify
from util import database
from util.taxonomy import MappingType
import util.common as utility

from hypertext import Where, Side

# pylint: disable=protected-access


_TREE = {}


def get_tree():
    '''full image tree'''
    if not _TREE:
        _TREE['tree'] = collection.build_image_tree()

    return copy.deepcopy(_TREE['tree'])


class TestHypertext(unittest.TestCase):
    '''hypertext.py'''

    def test_lineage_to_link(self):
        '''converting lineage to links between sites'''
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
        '''html titles ordering'''
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

    def test_title_ordinary(self):
        '''typical common name'''
        # gallery
        html, title = hypertext.title(
            ['heart', 'crab'], Where.Gallery, TestGallery.g_scientific
        )
        self.assertEqual(title, 'heart crab')
        self.assertIn('<title>Heart Crab</title>', html)
        self.assertIn('"top">Heart<', html)
        self.assertIn('"top">Crab<', html)
        self.assertNotIn('<em>', html)

    def test_title_scientific_common_name(self):
        '''some gallery entries may use scientific names when there isn't a
        common name available
        '''
        # gallery
        html, title = hypertext.title(
            ['tubastraea coccinea', 'coral'],
            Where.Gallery,
            TestGallery.g_scientific,
        )
        self.assertEqual(title, 'tubastraea coccinea coral')
        self.assertIn('<title>Tubastraea coccinea Coral</title>', html)
        self.assertIn('"top"><em>Tubastraea coccinea</em><', html)
        self.assertNotIn('Coccinea', html)

    def test_title_scientific_sp(self):
        '''it works'''
        # taxonomy
        html, title = hypertext.title(
            ['Animalia', 'Cnidaria', 'Anthozoa', 'Actiniaria', 'sp.'],
            Where.Taxonomy,
            TestGallery.t_scientific,
        )
        self.assertTrue(title.startswith('Animalia Cnidaria Anthozoa'), title)
        self.assertTrue(title.endswith('Actiniaria sp.'), title)

        self.assertIn('<title>Actiniaria sp.</title>', html)
        self.assertIn('>Anemone<', html)

    def test_title_names(self):
        '''html titles top level'''
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
    '''gallery.py'''

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def test_find_representative(self):
        '''picking the newest image to represent a tree, or a predefined
        'pinned' image
        '''
        tree = get_tree()

        self.assertIn('fish', tree)
        out = gallery.find_representative(tree['fish'], lineage=['fish'])
        self.assertEqual(out.name, 'Yellow Eye Rockfish')

        self.assertIn('barnacle', tree)
        out = gallery.find_representative(
            tree['barnacle'], lineage=['barnacle']
        )
        self.assertIsNotNone(out)

    def test_html_tree_gallery(self):
        '''basics'''
        tree = get_tree()
        sub_tree = tree['coral']
        htmls = gallery.html_tree(
            sub_tree, Where.Gallery, TestGallery.g_scientific, ['coral']
        )

        self.assertNotEqual(htmls, [])
        (path, html) = htmls[-1]

        self.assertEqual(path, 'coral.html')
        self.assertRegex(
            html, r'(?s)<head>.*<title>.*Coral.*</title>.*</head>'
        )
        self.assertRegex(html, r'(?s)<h3>.*Fan.*</h3>')
        self.assertRegex(html, r'(?s)<h3>.*Rhizopsammia wellingtoni.*</h3>')


class TestTaxonomy(unittest.TestCase):
    '''taxonomy.py'''

    def test_filter_exact(self):
        '''remove sp. entries'''
        tree = {'Actiniaria': {'sp.': 1, 'Actinioidea': 2, 'Metridioidea': 3}}
        tree = taxonomy._filter_exact(tree)
        self.assertEqual(
            tree, {'Actiniaria': {'Actinioidea': 2, 'Metridioidea': 3}}
        )

    def test_gallery_scientific(self):
        '''find scientific names by common name'''
        samples = [
            (['copper', 'rock', 'fish'], 'Sebastes caurinus'),
            (['fish'], 'Actinopterygii sp.'),
            (['fish', 'eggs'], 'Actinopterygii sp.'),
            (['juvenile yellow eye', 'rock', 'fish'], 'Sebastes ruberrimus'),
            (['noble', 'sea lemon', 'nudibranch'], 'Peltodoris nobilis'),
            (['brain', 'coral'], 'Scleractinia Mussidae'),
            (['multicolor', 'dendronotid', 'nudibranch'], 'diversicolor'),
            (['six rayed', 'star'], 'hexactis'),
            (['mossy', 'chiton'], 'muscosa'),
            (['mossy', 'chiton'], 'muscosa'),
            (['stone', 'fish'], 'plumieri mystes'),
        ]

        for lineage, output in samples:
            match = taxonomy.gallery_scientific(
                lineage, TestGallery.g_scientific
            )
            self.assertTrue(match.endswith(output), match)

    def test_similar(self):
        '''can these be collapsed?'''
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
        '''remove similar non-ambiguous names'''
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

    def test_title_scientific_name(self):
        '''cached helper'''
        for example in ('crab', 'fish', 'giant pacific octopus'):
            self.assertIsNone(taxonomy.is_scientific_name(example), example)

        for example in ('acanthodoris hudsoni', 'antipathes galapagensis'):
            self.assertIsNotNone(taxonomy.is_scientific_name(example), example)

        for example in ('pavona', 'porites'):
            self.assertIsNotNone(taxonomy.is_scientific_name(example), example)

    def test_binomial_names(self):
        '''parse binomial names from taxonomy.yml'''
        names = list(taxonomy.binomial_names())
        self.assertNotEqual(names, [])

        self.assertNotIn('crab', names)
        self.assertNotIn('Acanthodoris', names)
        self.assertIn('Acanthodoris hudsoni', names)


class TestImage(unittest.TestCase):
    '''image.py'''

    def test_categorize(self):
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

    def test_unqualify(self):
        '''remove qualifiers'''
        samples = [
            ("juvenile red octopus egg", "red octopus"),
            ("dead male kelp greenling", "kelp greenling"),
            ("giant pacific octopus", "giant pacific octopus"),
        ]
        for before, after in samples:
            self.assertEqual(image.unqualify(before), after)

    def test_split(self):
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

    def test_image_location(self):
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

    def test_image_site(self):
        '''it works'''
        samples = [
            ("2021-11-05 Rockaway Beach", "Rockaway Beach"),
            ("2021-11-05 1 Rockaway Beach", "Rockaway Beach"),
            ("2021-11-05 10 Rockaway Beach", "Rockaway Beach"),
        ]
        for before, after in samples:
            picture = image.Image('fish', before)
            self.assertEqual(picture.site(), after)

    def test_image_singular(self):
        '''it works'''
        samples = [
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

    def test_image_simplified(self):
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


class TestUtility(unittest.TestCase):
    '''utility.py'''

    def test_prefix_tuples(self):
        '''it works'''
        out = utility.prefix_tuples(1, [(2, 3), (3, 4), (4, 5)])
        out = list(out)
        self.assertEqual(out, [(1, 2, 3), (1, 3, 4), (1, 4, 5)])

    def test_take(self):
        '''it works'''
        self.assertEqual([0, 1, 2], utility.take(range(10), 3))

    def test_flatten(self):
        '''it works'''
        self.assertEqual([0, 1, 2], utility.flatten([[0], [1, 2]]))
        self.assertEqual([], utility.flatten([[]]))

    def test_tree_size(self):
        '''how many leaves are in this tree'''
        tree = {'a': {'b': [3, 3]}, 'c': [4, 4, 4]}
        self.assertEqual(utility.tree_size(tree), 5)

    def test_extract_leaves(self):
        '''grab the leaves for this tree'''
        tree = {'a': {'b': 3}, 'c': 4}
        leaves = list(utility.extract_leaves(tree))
        wanted = [3, 4]
        self.assertEqual(sorted(leaves), sorted(wanted))

    def test_extract_branches(self):
        '''grab the branches for this tree'''
        tree = {'a': {'b': 3}, 'c': 4}
        branches = list(utility.extract_branches(tree))
        wanted = ['a', 'b', 'c']
        self.assertEqual(sorted(branches), sorted(wanted))

    def test_hmap(self):
        '''fold-ish thing'''
        out = utility.hmap(0, lambda x: x + 1, lambda x: x * 5)
        self.assertEqual(out, 5)

    def test_is_date(self):
        '''it works'''
        for positive in ('2017-01-01', '2000-11-21'):
            self.assertTrue(utility.is_date(positive))

        for negative in ('2000-91-21', '2000-21', '2000-21'):
            self.assertFalse(utility.is_date(negative))

    def test_strip_date(self):
        '''it works'''
        examples = [
            ('Sund Rock 2017-01-01', 'Sund Rock'),
            ('Sund Rock 4', 'Sund Rock 4'),
        ]
        for before, after in examples:
            self.assertEqual(utility.strip_date(before), after)


class TestInformation(unittest.TestCase):
    '''information.py'''

    def test_lineage_to_names(self):
        '''extract the right parts for look up'''
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
    '''locations.py'''

    def test_add_context(self):
        '''add_context'''
        samples = [
            ('Edmonds', 'Washington Edmonds'),
            ('Bonaire Oil Slick', 'Bonaire Oil Slick'),
            ('Klein Bonaire M', 'Bonaire Klein Bonaire M'),
            ('Rockaway Stretch Reef', 'Washington Rockaway Stretch Reef'),
        ]
        for before, after in samples:
            self.assertEqual(locations.add_context(before), after)

    def test_strip_date(self):
        '''strip_date'''


class TestCollection(unittest.TestCase):
    '''collection.py'''


class TestVerify(unittest.TestCase):
    '''verify.py'''

    def _build_swapped_tree(self):
        '''swapped words'''
        tree = get_tree()
        nudi = tree['nudibranch']['sea lemon']['freckled pale']['data'].pop()
        nudi.name = 'Pale Freckled Sea Lemon'

        tree['nudibranch']['sea lemon']['pale freckled'] = {'data': [nudi]}

        self.assertIn('pale freckled', tree['nudibranch']['sea lemon'].keys())
        self.assertIn('freckled pale', tree['nudibranch']['sea lemon'].keys())

        return tree

    def test_detect_wrong_name_order(self):
        '''pale freckled sea lemon vs freckled pale sea lemon'''
        tree = self._build_swapped_tree()
        wrong = list(verify._find_wrong_name_order(tree))
        self.assertEqual(wrong, [('freckled pale', 'pale freckled')])

    def test_detect_misspelling(self):
        '''curlyhead spaghetti worm vs curlyheaded spaghetti worm'''
        examples = [
            ['curlyhead spaghetti worm', 'curlyheaded spaghetti worm'],
            ['encrusting bryozoan', 'encrusting byrozoan'],
            ['nanaimo nudibranch', 'naniamo nudibranch'],
        ]
        for names in examples:
            wrong = [
                sorted(w) for w in verify._possible_misspellings(names[:])
            ]
            self.assertEqual(wrong, [names])

    def test_detect_misspelling_ignore_explicit(self):
        '''don't consider ignored names'''
        examples = [
            ['submerged log', 'submerged wood'],
            ['a unknown', 'b unknown'],
        ]
        for names in examples:
            wrong = [
                sorted(w) for w in verify._possible_misspellings(names[:])
            ]
            self.assertEqual(wrong, [])

    def test_detect_misspelling_ignore_scientific(self):
        '''a name isn't misspelled if it has a scientific name'''
        examples = [
            ['dalls dendronotid nudibranch', 'red dendronotid nudibranch'],
        ]
        for names in examples:
            wrong = [sorted(w) for w in verify._find_misspellings(names[:])]
            self.assertEqual(wrong, [])


if __name__ == '__main__':
    database.use_test_database()
    unittest.main()
