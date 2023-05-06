# type: ignore
'''
Sanity checks
'''

import os
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
from util import static
from util.taxonomy import MappingType
import util.common as utility

from hypertext import Where, Side

# pylint: disable=protected-access,missing-docstring


_TREE = {}


def get_tree():
    '''full image tree'''
    if not _TREE:
        _TREE['tree'] = collection.build_image_tree()

    return copy.deepcopy(_TREE['tree'])


class TestStatic(unittest.TestCase):
    '''static.py'''

    def writer(self, path: str, body: str) -> None:
        '''write a file, track it for cleanup'''
        if path not in self.written:
            self.written.append(path)

        with open(path, 'w+') as fd:
            print(body, end='', file=fd)

    def setUp(self) -> None:
        self.written = []
        self.writer('/tmp/versioned.bin', 'applesauce')

    def tearDown(self) -> None:
        for path in self.written:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_versioned_css(self):
        vr = static.VersionedResource(utility.source_root + 'web/style.css')
        self.assertEqual(vr._name, 'style.css')
        self.assertIn('display: inline-block;', vr._body)
        self.assertEqual(len(vr._hash), 10)
        self.assertEqual(vr.path, f'style-{vr._hash}.css')

    def test_does_not_overwrite_identical(self):
        vr = static.VersionedResource('/tmp/versioned.bin', '/tmp')
        self.assertEqual(vr.path, '/tmp/versioned-404a6e35ea.bin')

        self.writer(vr.path, 'applesauce')
        vr.write()
        st1 = os.stat(vr.path)

        vr.write()
        vr.write()
        st2 = os.stat(vr.path)

        self.assertEqual(st1.st_mtime, st2.st_mtime)

    def test_finds_versions_with_glob(self):
        seen = []

        for body in range(0, 10):
            self.writer('/tmp/versioned.bin', str(body))

            vr = static.VersionedResource('/tmp/versioned.bin', '/tmp')
            self.assertNotIn(vr.path, seen)
            seen.append(vr.path)
            self.written.append(vr.path)
            vr.write()

        self.assertEqual(len(seen), 10)
        self.assertEqual(vr.versions(), seen[::-1])

    def test_cleans_up_old_versions(self):
        for body in range(0, 10):
            self.writer('/tmp/versioned.bin', str(body))

            vr = static.VersionedResource('/tmp/versioned.bin', '/tmp')
            self.written.append(vr.path)
            vr.write()

        self.assertEqual(len(vr.versions()), 10)
        vr.cleanup(3)

        retained = vr.versions()
        self.assertEqual(len(retained), 3)
        self.assertEqual(retained, self.written[-3:][::-1])


class TestHypertext(unittest.TestCase):
    '''hypertext.py'''

    def test_image_to_name_html(self):
        '''it works'''
        utility._EXISTS['gallery/rock-fish.html'] = True

        fish = image.Image(
            "001 - Rockfish.jpg", "2021-11-05 10 Rockaway Beach"
        )
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

    def test_switcher_button(self):
        '''See that the correct HTML is generated for each site's button'''
        for where in Where:
            shorter = hypertext.switcher_button(where)
            self.assertIn(f'href="/{where.name.lower()}/index.html"', shorter)
            self.assertNotIn(where.name, shorter)

            longer = hypertext.switcher_button(where, long=True)
            self.assertIn(f'href="/{where.name.lower()}/index.html"', longer)
            self.assertIn(where.name, longer)


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
        tree = get_tree()
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
        tree = get_tree()
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
            self.assertTrue(
                taxonomy.looks_like_scientific_name(sample), sample
            )

        negatives = ['Fairy Palm Hydroid']
        for sample in negatives:
            self.assertFalse(
                taxonomy.looks_like_scientific_name(sample), sample
            )

    def test_filter_exact(self):
        '''remove sp. entries'''
        tree = {'Actiniaria': {'sp.': 1, 'Actinioidea': 2, 'Metridioidea': 3}}
        tree = taxonomy._filter_exact(tree)
        self.assertEqual(
            tree, {'Actiniaria': {'Actinioidea': 2, 'Metridioidea': 3}}
        )

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
            match = taxonomy.gallery_scientific(
                lineage, TestGallery.g_scientific
            )
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

    def test_walk_spine(self):
        '''it works'''
        tree = {'a': {'b': {'c': 1}}}
        self.assertEqual(utility.walk_spine(tree, ['a']), {'b': {'c': 1}})
        self.assertEqual(utility.walk_spine(tree, ['a', 'b']), {'c': 1})
        self.assertEqual(utility.walk_spine(tree, ['a', 'b', 'c']), 1)

    def test_prefix_tuples(self):
        '''it works'''
        out = utility.prefix_tuples(1, [(2, 3), (3, 4), (4, 5)])
        out = list(out)
        self.assertEqual(out, [(1, 2, 3), (1, 3, 4), (1, 4, 5)])

    def test_pretty_date(self):
        pairs = [
            ('2023-01-01', 'January 1st, 2023'),
            ('2023-01-11', 'January 11th, 2023'),
            ('2023-01-12', 'January 12th, 2023'),
            ('2023-01-13', 'January 13th, 2023'),
            ('2023-10-02', 'October 2nd, 2023'),
            ('2023-10-22', 'October 22nd, 2023'),
            ('2023-12-03', 'December 3rd, 2023'),
            ('2023-12-23', 'December 23rd, 2023'),
            ('2023-04-04', 'April 4th, 2023'),
            ('2023-04-24', 'April 24th, 2023'),
        ]
        for before, after in pairs:
            self.assertEqual(utility.pretty_date(before), after)

    def test_take(self):
        '''it works'''
        xs = [1, 2, 3, 4, 5]
        n = 3
        expected = [1, 2, 3]
        self.assertEqual(utility.take(xs, n), expected)

        xs = [1, 2, 3]
        n = 5
        expected = [1, 2, 3]
        self.assertEqual(utility.take(xs, n), expected)

        xs = [1, 2, 3, 4, 5]
        n = 0
        expected = []
        self.assertEqual(utility.take(xs, n), expected)

        xs = range(100000000)
        n = 5
        expected = [0, 1, 2, 3, 4]
        self.assertEqual(utility.take(xs, n), expected)

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

    def test_expand_names(self):
        '''it works'''
        base = image.Image(
            "001 - Fish and Coral.jpg", "2021-11-05 10 Rockaway Beach"
        )
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 2)
        fish = out[0]
        coral = out[1]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(coral.name, 'Coral')
        self.assertEqual(fish.number, coral.number)
        self.assertEqual(fish.directory, coral.directory)

    def test_expand_names_noop(self):
        '''it works'''
        base = image.Image("001 - Fish", "2021-11-05 10 Rockaway Beach")
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 1)
        fish = out[0]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(fish.number, '001')


class TestVerify(unittest.TestCase):
    '''verify.py'''

    def setUp(self):
        database.use_test_database()

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
