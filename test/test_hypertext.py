# type: ignore

import unittest

import hypertext

from util import image
from util import taxonomy
from util.taxonomy import MappingType
from hypertext import Where, Side

import util.common as utility


class TestHypertext(unittest.TestCase):
    '''hypertext.py'''

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

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
                scientific = TestHypertext.g_scientific
            else:
                scientific = TestHypertext.t_scientific

            html, title = hypertext.title(lineage, where, scientific)

            indices = [html.find(e) for e in elements]
            self.assertEqual(indices, sorted(indices), lineage)
            self.assertEqual(title, ' '.join(lineage))

    def test_title_ordinary(self):
        '''typical common name'''
        # gallery
        html, title = hypertext.title(
            ['heart', 'crab'], Where.Gallery, TestHypertext.g_scientific
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
            TestHypertext.g_scientific,
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
            TestHypertext.t_scientific,
        )
        self.assertTrue(title.startswith('Animalia Cnidaria Anthozoa'), title)
        self.assertTrue(title.endswith('Actiniaria sp.'), title)

        self.assertIn('<title>Actiniaria sp.</title>', html)
        self.assertIn('>Anemone<', html)

    def test_title_names(self):
        '''html titles top level'''
        # gallery
        html, title = hypertext.title([], Where.Gallery, TestHypertext.g_scientific)
        self.assertEqual(title, 'Gallery')
        self.assertIn('<title>Gallery</title>', html)

        # taxonomy
        html, title = hypertext.title([], Where.Taxonomy, TestHypertext.t_scientific)
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


if __name__ == '__main__':
    unittest.main()
