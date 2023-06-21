# type: ignore

import copy
import unittest

import gallery
import information
import hypertext

from util import collection
from util import database
from util import taxonomy
from util import image

from util.taxonomy import MappingType
from hypertext import Where, Side

import util.common as utility


_TREE_CACHE = None


def build_image_tree():
    '''cached!'''
    global _TREE_CACHE
    if _TREE_CACHE is None:
        _TREE_CACHE = collection.build_image_tree()

    return copy.deepcopy(_TREE_CACHE)


class TestHypertext(unittest.TestCase):
    '''hypertext.py'''

    def test_image_to_name_html(self):
        '''it works'''
        utility._EXISTS['gallery/rock-fish.html'] = True

        fish = image.Image("001 - Rockfish.jpg", "2021-11-05 10 Rockaway Beach")
        html = hypertext.image_to_name_html(fish, Where.Sites)
        self.assertIn('href="/gallery/rock-fish.html"', html)
        self.assertIn('Rockfish', html)

    def test_image_to_name_html_pair(self):
        '''it works'''
        utility._EXISTS['gallery/rock-fish.html'] = True

        fish = image.Image(
            "001 - Rockfish and Coral.jpg", "2021-11-05 10 Rockaway Beach"
        )
        html = hypertext.image_to_name_html(fish, Where.Sites)
        self.assertIn('href="/gallery/rock-fish.html"', html)
        self.assertIn('Rockfish', html)

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
        html, title = hypertext.title([], Where.Gallery, TestGallery.g_scientific)
        self.assertEqual(title, 'Gallery')
        self.assertIn('<title>Gallery</title>', html)

        # taxonomy
        html, title = hypertext.title([], Where.Taxonomy, TestGallery.t_scientific)
        self.assertEqual(title, 'Taxonomy')
        self.assertIn('<title>Taxonomy</title>', html)

    def test_switcher_button(self):
        '''See that the correct HTML is generated for each site's button'''
        for where in Where:
            shorter = hypertext.switcher_button(where)
            self.assertIn(f'href="/{where.name.lower()}/index.html"', shorter)
            self.assertNotIn(where.name, shorter)

            longer = hypertext.switcher_button(where, long=True)
            self.assertIn(f'href="/{where.name.lower()}/index.html"', longer)
            self.assertIn(where.name, longer)


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


class TestGallery(unittest.TestCase):
    '''gallery.py'''

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def setUp(self):
        database.use_test_database()

    def test_find_representative(self):
        '''picking the newest image to represent a tree, or a predefined
        'pinned' image
        '''
        tree = build_image_tree()

        self.assertIn('fish', tree)
        out = gallery.find_representative(tree['fish'], lineage=['fish'])
        self.assertEqual(out.name, 'Yellow Eye Rockfish')

        self.assertIn('barnacle', tree)
        out = gallery.find_representative(tree['barnacle'], lineage=['barnacle'])
        self.assertIsNotNone(out)

    def test_key_to_subject_gallery(self):
        '''current element to visible text'''

        def key_to_subject(key):
            return gallery._key_to_subject(key, Where.Gallery)

        self.assertEqual(key_to_subject('fancy fish'), 'Fancy Fish')
        self.assertEqual(key_to_subject('octopus'), '<em>Octopus</em>')

    def test_key_to_subject_taxonomy(self):
        '''current element to visible text'''

        def key_to_subject(key):
            return gallery._key_to_subject(key, Where.Taxonomy)

        self.assertEqual(key_to_subject('octopoda octopus'), 'O. octopus')

    def test_key_to_subject_sites(self):
        '''current element to visible text'''

        def key_to_subject(key):
            return gallery._key_to_subject(key, Where.Sites)

        self.assertEqual(key_to_subject('Stretch Reef'), 'Stretch Reef')
        self.assertEqual(key_to_subject('Shallows 2021-03-06'), 'Shallows')
        self.assertEqual(key_to_subject('2021-03-06'), 'March 6th, 2021')

    def test_html_tree_gallery(self):
        '''basics'''
        tree = build_image_tree()
        sub_tree = tree['coral']
        htmls = gallery.html_tree(
            sub_tree, Where.Gallery, TestGallery.g_scientific, ['coral']
        )

        self.assertNotEqual(htmls, [])
        (path, html) = htmls[-1]

        self.assertEqual(path, 'coral.html')
        self.assertRegex(html, r'(?s)<head>.*<title>.*Coral.*</title>.*</head>')
        self.assertRegex(html, r'(?s)<h3.*Fan.*</h3>')
        self.assertRegex(html, r'(?s)<h3.*Rhizopsammia wellingtoni.*</h3>')


class TestTaxonomy(unittest.TestCase):
    '''taxonomy.py'''

    def setUp(self):
        database.use_test_database()

    def test_compress_single_leaf(self):
        tree = {"a": {"b": {"c": "d"}}}
        result = taxonomy.compress_tree(tree)
        self.assertEqual(result, {"a b c": "d"})

    def test_compress_single_subtree(self):
        tree = {"a": {"b": {"c": {"d": "e"}}}}
        result = taxonomy.compress_tree(tree)
        self.assertEqual(result, {"a b c d": "e"})

    def test_compress_multiple_subtrees(self):
        tree = {"a": {"b": {"c": {"d": "e", "f": "g"}}}}
        result = taxonomy.compress_tree(tree)
        self.assertEqual(result, {"a b c": {"d": "e", "f": "g"}})

    def test_compress_complex_tree(self):
        tree = {
            "a": {"b": {"c": "d", "e": {"f": "g", "h": {"i": "n"}}}, "j": "k"},
            "l": "m",
        }
        result = taxonomy.compress_tree(tree)
        expected = {
            "a": {"b": {"c": "d", "e": {"f": "g", "h i": "n"}}, "j": "k"},
            "l": "m",
        }
        self.assertEqual(result, expected)

    def test_find_representative(self):
        '''same as gallery.py but the lineage is reversed'''
        tree = build_image_tree()
        taxia = taxonomy.gallery_tree(tree)
        lineage = [
            'Animalia',
            'Cnidaria',
            'Hydrozoa',
            'Leptothecata',
            'Plumularioidea',
        ]
        self.assertIn('Animalia', taxia)
        self.assertIn('Cnidaria', taxia['Animalia'])

        for i in range(len(lineage)):
            out = gallery.find_representative(taxia, lineage=lineage[:i])
            self.assertIsNotNone(out)

    def test_taxia_filler(self):
        '''it doesn't lose data'''
        tree = build_image_tree()
        images = taxonomy.single_level(tree)
        taxia = taxonomy.compress_tree(taxonomy.load_tree())

        sub_taxia = utility.walk_spine(
            taxia,
            [
                'Animalia',
                'Cnidaria',
                'Hydrozoa',
                'Leptothecata',
                'Plumularioidea',
            ],
        )
        self.assertIsNotNone(sub_taxia)
        filled = taxonomy._taxia_filler(sub_taxia, images)

        self.assertIn('Aglaopheniidae', filled)
        self.assertNotEqual(filled['Aglaopheniidae'], {})

    def test_looks_like_scientific_name(self):
        '''it works'''
        positives = [
            'Aglaophenia diegensis Hydroid',
            'Antipathes galapagensis',
        ]
        for sample in positives:
            self.assertTrue(taxonomy.looks_like_scientific_name(sample), sample)

        negatives = ['Fairy Palm Hydroid']
        for sample in negatives:
            self.assertFalse(taxonomy.looks_like_scientific_name(sample), sample)

    def test_filter_exact(self):
        '''remove sp. entries'''
        tree = {'Actiniaria': {'sp.': 1, 'Actinioidea': 2, 'Metridioidea': 3}}
        tree = taxonomy._filter_exact(tree)
        self.assertEqual(tree, {'Actiniaria': {'Actinioidea': 2, 'Metridioidea': 3}})

    def test_mapping_gallery(self):
        ms = taxonomy.mapping(MappingType.Gallery)
        self.assertIn('fish', ms)
        self.assertEqual(ms['fish'], 'Animalia Chordata Actinopterygii sp.')

    def test_mapping_taxonomy(self):
        ms = taxonomy.mapping(MappingType.Taxonomy)
        self.assertIn('Animalia Chordata Actinopterygii sp.', ms)
        self.assertEqual(ms['Animalia Chordata Actinopterygii sp.'], 'fish')

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
            (['pacific', 'stone', 'fish'], 'plumieri mystes'),
        ]

        for lineage, output in samples:
            match = taxonomy.gallery_scientific(lineage, TestGallery.g_scientific)
            self.assertTrue(match.endswith(output), f'{match} != {output}')

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

    def test_simplify_shortens_very_long(self):
        samples = [
            (
                'Brachiopoda Rhynchonellata Terebratulida Laqueoidea '
                'Terebrataliidae Terebratalia transversa',
                'Brachiopoda ... transversa',
            ),
            (
                'Chromista Ochrophyta Bacillariophyceae Cymbellales '
                'Gomphonemataceae Didymosphenia geminata',
                'Chromista ... geminata',
            ),
        ]
        for before, after in samples:
            self.assertEqual(after, taxonomy.simplify(before, shorten=True))

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


if __name__ == '__main__':
    unittest.main()
