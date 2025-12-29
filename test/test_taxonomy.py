# type: ignore

import pytest

import diving.util.common as utility
from diving import gallery
from diving.hypertext import Where
from diving.util import collection, taxonomy
from diving.util.taxonomy import MappingType

g_scientific = taxonomy.mapping()
t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)


class TestTaxonomy:
    """taxonomy.py"""

    def test_compress_single_leaf(self):
        tree = {'a': {'b': {'c': 'd'}}}
        result = taxonomy.compress_tree(tree)
        assert result == {'a b c': 'd'}

    def test_compress_single_subtree(self):
        tree = {'a': {'b': {'c': {'d': 'e'}}}}
        result = taxonomy.compress_tree(tree)
        assert result == {'a b c d': 'e'}

    def test_compress_multiple_subtrees(self):
        tree = {'a': {'b': {'c': {'d': 'e', 'f': 'g'}}}}
        result = taxonomy.compress_tree(tree)
        assert result == {'a b c': {'d': 'e', 'f': 'g'}}

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
        assert result == expected

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
        assert 'Animalia' in taxia
        assert 'Cnidaria' in taxia['Animalia']

        for i in range(len(lineage)):
            out = gallery.find_representative(taxia, Where.Taxonomy, lineage=lineage[:i])
            assert out is not None

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
        assert sub_taxia is not None
        filled = taxonomy._taxia_filler(sub_taxia, images)

        assert 'Aglaopheniidae' in filled
        assert filled['Aglaopheniidae'] != {}

    @pytest.mark.parametrize(
        'name',
        [
            'Aglaophenia diegensis Hydroid',
            'Antipathes galapagensis',
        ],
    )
    def test_looks_like_scientific_name_positive(self, name: str):
        """it works - positive cases"""
        assert taxonomy.looks_like_scientific_name(name) is True

    @pytest.mark.parametrize(
        'name',
        [
            'Fairy Palm Hydroid',
        ],
    )
    def test_looks_like_scientific_name_negative(self, name: str):
        """it works - negative cases"""
        assert taxonomy.looks_like_scientific_name(name) is False

    def test_filter_exact(self):
        """remove sp. entries"""
        tree = {'Actiniaria': {'sp.': 1, 'Actinioidea': 2, 'Metridioidea': 3}}
        tree = taxonomy._filter_exact(tree)
        assert tree == {'Actiniaria': {'Actinioidea': 2, 'Metridioidea': 3}}

    def test_mapping_gallery(self):
        ms = taxonomy.mapping(MappingType.Gallery)
        assert 'fish' in ms
        assert ms['fish'] == 'Animalia Chordata Actinopterygii sp.'

    def test_mapping_taxonomy(self):
        ms = taxonomy.mapping(MappingType.Taxonomy)
        assert 'Animalia Chordata Actinopterygii sp.' in ms
        assert ms['Animalia Chordata Actinopterygii sp.'] == 'fish'

    @pytest.mark.parametrize(
        'lineage,expected',
        [
            (['copper', 'rock', 'fish'], 'Sebastes caurinus'),
            (['fish'], 'Actinopterygii sp.'),
            (['eggs', 'fish'], 'Actinopterygii sp.'),
            (['juvenile yellow eye', 'rock', 'fish'], 'Sebastes ruberrimus'),
            (['noble', 'sea lemon', 'nudibranch'], 'Peltodoris nobilis'),
            (['brain', 'coral'], 'Scleractinia Mussidae'),
            (['multicolor', 'dendronotid', 'nudibranch'], 'diversicolor'),
            (['six rayed', 'star'], 'hexactis'),
            (['mossy', 'chiton'], 'muscosa'),
            (['pacific', 'stone', 'fish'], 'Scorpaena mystes'),
            (['feather', 'star'], 'Echinodermata Crinoidea sp.'),
        ],
    )
    def test_gallery_scientific(self, lineage: list[str], expected: str):
        """find scientific names by common name"""
        match = taxonomy.gallery_scientific(lineage, g_scientific)
        assert match.endswith(expected), f'{match} != {expected}'

    @pytest.mark.parametrize(
        'expected,pair',
        [
            (True, ('Amphinomida', 'Amphinomidae')),
            (True, ('Aphrocallistidae', 'Aphrocallistes')),
            (True, ('Clionaida', 'Clionaidae')),
            (True, ('Membraniporoidea', 'Membraniporidae')),
            (True, ('Strongylocentrotidae', 'Strongylocentrotus')),
            (False, ('Comatulida', 'Antedonidae')),
            (False, ('Toxopneustidae', 'Tripneustes')),
        ],
    )
    def test_similar(self, expected: bool, pair: tuple[str, str]):
        """can these be collapsed?"""
        a, b = pair
        assert taxonomy.similar(a, b) == expected

    @pytest.mark.parametrize(
        'before,after',
        [
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
        ],
    )
    def test_simplify(self, before: str, after: str):
        """remove similar non-ambiguous names"""
        assert taxonomy.simplify(before) == after

    @pytest.mark.parametrize(
        'before,after',
        [
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
        ],
    )
    def test_simplify_shortens_very_long(self, before: str, after: str):
        assert taxonomy.simplify(before, shorten=True) == after

    @pytest.mark.parametrize(
        'example',
        [
            'crab',
            'fish',
            'giant pacific octopus',
        ],
    )
    def test_is_scientific_name_negative(self, example: str):
        """cached helper - non-scientific names"""
        assert taxonomy.is_scientific_name(example) is None

    @pytest.mark.parametrize(
        'example',
        [
            'acanthodoris hudsoni',
            'antipathes galapagensis',
        ],
    )
    def test_is_scientific_name_positive(self, example: str):
        """cached helper - scientific names"""
        assert taxonomy.is_scientific_name(example) is not None

    @pytest.mark.parametrize(
        'example',
        [
            'pavona',
            'porites',
        ],
    )
    def test_is_scientific_name_genus(self, example: str):
        """cached helper - genus names"""
        assert taxonomy.is_scientific_name(example) is not None

    def test_binomial_names(self):
        """parse binomial names from taxonomy.yml"""
        names = list(taxonomy.binomial_names())
        assert names != []

        assert 'crab' not in names
        assert 'Acanthodoris' not in names
        assert 'Acanthodoris hudsoni' in names

    @pytest.mark.parametrize(
        'word',
        [
            'acanthodoris',
            'hudsoni',
            'mopaliidae',
            'polychaeta',
            'annelida',
        ],
    )
    def test_all_latin_words(self, word: str) -> None:
        words = taxonomy.all_latin_words()
        assert word in words

    def test_all_latin_words_excludes_common(self) -> None:
        words = taxonomy.all_latin_words()
        assert 'moon snail' not in words
