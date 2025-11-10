# type: ignore

import unittest

import gallery
import util.common as utility
from hypertext import Where
from util import collection, database, taxonomy
from util.taxonomy import MappingType


class TestTaxonomy(unittest.TestCase):
    """taxonomy.py"""

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def setUp(self):
        database.use_test_database()

    def test_compress_single_leaf(self):
        tree = {'a': {'b': {'c': 'd'}}}
        result = taxonomy.compress_tree(tree)
        self.assertEqual(result, {'a b c': 'd'})

    def test_compress_single_subtree(self):
        tree = {'a': {'b': {'c': {'d': 'e'}}}}
        result = taxonomy.compress_tree(tree)
        self.assertEqual(result, {'a b c d': 'e'})

    def test_compress_multiple_subtrees(self):
        tree = {'a': {'b': {'c': {'d': 'e', 'f': 'g'}}}}
        result = taxonomy.compress_tree(tree)
        self.assertEqual(result, {'a b c': {'d': 'e', 'f': 'g'}})

    def test_compress_complex_tree(self):
        tree = {
            'a': {'b': {'c': 'd', 'e': {'f': 'g', 'h': {'i': 'n'}}}, 'j': 'k'},
            'l': 'm',
        }
        result = taxonomy.compress_tree(tree)
        expected = {
            'a': {'b': {'c': 'd', 'e': {'f': 'g', 'h i': 'n'}}, 'j': 'k'},
            'l': 'm',
        }
        self.assertEqual(result, expected)

    def test_find_representative(self):
        """same as gallery.py but the lineage is reversed"""
        taxia = taxonomy.gallery_tree()
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
            out = gallery.find_representative(taxia, Where.Taxonomy, lineage=lineage[:i])
            self.assertIsNotNone(out)

    def test_taxia_filler(self):
        """it doesn't lose data"""
        images = collection.single_level(collection.build_image_tree())
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
        """it works"""
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
        """remove sp. entries"""
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
        """find scientific names by common name"""
        samples = [
            (['copper', 'rock', 'fish'], 'Sebastes caurinus'),
            (['fish'], 'Actinopterygii sp.'),
            (['eggs', 'fish'], 'Actinopterygii sp.'),
            (['juvenile yellow eye', 'rock', 'fish'], 'Sebastes ruberrimus'),
            (['noble', 'sea lemon', 'nudibranch'], 'Peltodoris nobilis'),
            (['brain', 'coral'], 'Scleractinia Mussidae'),
            (['multicolor', 'dendronotid', 'nudibranch'], 'diversicolor'),
            (['six rayed', 'star'], 'hexactis'),
            (['mossy', 'chiton'], 'muscosa'),
            (['pacific', 'stone', 'fish'], 'plumieri mystes'),
            (['feather', 'star'], 'Echinodermata Crinoidea sp.'),
        ]

        for lineage, output in samples:
            match = taxonomy.gallery_scientific(lineage, TestTaxonomy.g_scientific)
            self.assertTrue(match.endswith(output), f'{match} != {output}')

    def test_similar(self):
        """can these be collapsed?"""
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
        """remove similar non-ambiguous names"""
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
        """cached helper"""
        for example in ('crab', 'fish', 'giant pacific octopus'):
            self.assertIsNone(taxonomy.is_scientific_name(example), example)

        for example in ('acanthodoris hudsoni', 'antipathes galapagensis'):
            self.assertIsNotNone(taxonomy.is_scientific_name(example), example)

        for example in ('pavona', 'porites'):
            self.assertIsNotNone(taxonomy.is_scientific_name(example), example)

    def test_binomial_names(self):
        """parse binomial names from taxonomy.yml"""
        names = list(taxonomy.binomial_names())
        self.assertNotEqual(names, [])

        self.assertNotIn('crab', names)
        self.assertNotIn('Acanthodoris', names)
        self.assertIn('Acanthodoris hudsoni', names)

    def test_all_latin_words(self) -> None:
        words = taxonomy.all_latin_words()

        latin_words = [
            'acanthodoris',
            'hudsoni',
            'mopaliidae',
            'polychaeta',
            'annelida',
        ]
        for word in latin_words:
            self.assertIn(word, words)

        self.assertNotIn('moon snail', words)


if __name__ == '__main__':
    unittest.main()
