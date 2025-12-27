# type: ignore

import unittest

from diving import hypertext
from diving.hypertext import Side, Where
from diving.util import taxonomy
from diving.util.taxonomy import MappingType


class TestHypertext(unittest.TestCase):
    """hypertext.py"""

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def test_description_sites(self):
        organized = ', organized by dive site and date'
        pairs = [
            ('Maldives', f'Maldives{organized}'),
            ('British Columbia', f'British Columbia{organized}'),
            (
                'British Columbia Aquarium 2023-04-02',
                'Aquarium, British Columbia on April 2nd, 2023',
            ),
            (
                'Washington Rockaway Stretch Reef 2021-11-20',
                'Rockaway Stretch Reef, Washington on November 20th, 2021',
            ),
            ('Galapagos Fernandina', f'Fernandina, Galapagos{organized}'),
            (
                'Galapagos Isabella Punta Vicente Roca 2021-08-28',
                'Isabella Punta Vicente Roca, Galapagos on August 28th, 2021',
            ),
            ('Bonaire Klein M', f'Klein M, Bonaire{organized}'),
            (
                'Bonaire One Thousand Steps 2021-07-04',
                'One Thousand Steps, Bonaire on July 4th, 2021',
            ),
        ]
        for name, description in pairs:
            expect = f'Explore high quality scuba diving pictures from {description}.'
            self.assertEqual(hypertext.description(name, Where.Sites), expect)

    def test_description_gallery(self):
        pairs = [
            ('Red Rock Crab', 'Red Rock Crabs'),
            ("Heath's Dorid Nudibranch", "Heath's Dorid Nudibranchs"),
            ('Various Red Octopus', 'Red Octopus'),
            ('Tubastraea coccinea Coral', 'Tubastraea coccinea Corals'),
        ]
        for name, description in pairs:
            expect = (
                f'Explore high quality scuba diving pictures of {description} '
                'and related organisms.'
            )
            self.assertEqual(hypertext.description(name, Where.Gallery), expect)

    def test_description_taxonomy(self):
        pairs = [
            ('Animalia', 'members of Animalia'),
            ('Malacostraca Decapoda', 'members of Malacostraca Decapoda'),
            (
                'Alpheoidea Alpheidae Alpheus djeddensis',
                'Alpheus djeddensis and related organisms',
            ),
            ('Cancer antennarius', 'Cancer antennarius and related organisms'),
        ]
        for name, description in pairs:
            expect = f'Explore high quality scuba diving pictures of {description}.'
            self.assertEqual(hypertext.description(name, Where.Taxonomy), expect)

    def test_lineage_to_link(self):
        """converting lineage to links between sites"""
        samples = [
            (None, False, ['a', 'b', 'c'], 'a-b-c'),
            (None, True, ['a', 'b', 'c'], 'a-b-c'),
            ('d', False, ['a', 'b', 'c'], 'd-a-b-c'),
            ('d', True, ['a', 'b', 'c'], 'a-b-c-d'),
        ]
        for key, right_side, lineage, after in samples:
            side = Side.Right if right_side else Side.Left
            link = hypertext.lineage_to_link(lineage, side, key)
            self.assertEqual(link, after)

    def skip_title_ordering(self):
        """html titles ordering"""
        samples = [
            (
                # gallery simple case
                Where.Gallery,
                ['chiton'],
                ['chiton', 'buffer', 'gallery/'],
            ),
            (
                # gallery multi level
                Where.Gallery,
                ['brittle', 'star'],
                ['brittle-star', 'buffer', 'gallery/'],
            ),
            (
                # gallery, has scientific name
                Where.Gallery,
                ['giant pacific', 'octopus'],
                [
                    'gallery/giant-pacific',
                    'gallery/octopus',
                    'gallery/',
                    (
                        'Animalia-Mollusca-Cephalopoda-Octopoda-Octopodoidea-'
                        'Enteroctopodidae-Enteroctopus-dofleini'
                    ),
                ],
            ),
            (
                # taxonomy, simple case
                Where.Taxonomy,
                ['Animalia'],
                ['taxonomy/', 'Animalia'],
            ),
            (
                # taxonomy, no common name
                Where.Taxonomy,
                ['Animalia', 'Echinodermata'],
                [
                    'taxonomy/',
                    'Animalia',
                    'Animalia-Echinodermata',
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
                    'taxonomy/',
                    'Animalia',
                    'Animalia-Mollusca',
                    # a ton more stuff
                    'giant-pacific-octopus',
                ],
            ),
        ]
        for where, lineage, elements in samples:
            if where == Where.Gallery:
                scientific = TestHypertext.g_scientific
            else:
                scientific = TestHypertext.t_scientific

            html, title = hypertext.title(lineage, where, scientific)

            indices = [html.find('href="/' + e) for e in elements]
            self.assertEqual(indices, sorted(indices), lineage)
            self.assertEqual(title, ' '.join(lineage))

    def test_title_names(self):
        """html titles top level"""
        # gallery
        html, path = hypertext.title([], Where.Gallery, TestHypertext.g_scientific)
        self.assertEqual(path, 'gallery/index.html')
        self.assertIn('<title>Gallery</title>', html)

        # taxonomy
        html, path = hypertext.title([], Where.Taxonomy, TestHypertext.t_scientific)
        self.assertEqual(path, 'taxonomy/index.html')
        self.assertIn('<title>Taxonomy</title>', html)

    def test_switcher_button(self):
        """See that the correct HTML is generated for each site's button"""
        for where in Where:
            shorter = hypertext.switcher_button(where)
            self.assertIn(f'href="/{where.name.lower()}/"', shorter)
            self.assertNotIn(where.name, shorter)

            longer = hypertext.switcher_button(where, long=True)
            self.assertIn(f'href="/{where.name.lower()}/"', longer)
            self.assertIn(where.name, longer)

    def test_top_timeline_spacing(self):
        html, title = hypertext.title([], Where.Timeline, TestHypertext.g_scientific)
        self.assertNotIn('scientific', html)

    def test_top_gallery_search_bar(self):
        html, title = hypertext.title([], Where.Gallery, TestHypertext.g_scientific)
        self.assertIn('input type="text"', html)


class TestTitleGallery(unittest.TestCase):
    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def test_title_ordinary(self):
        """typical common name"""
        html, path = hypertext.title(['heart', 'crab'], Where.Gallery, TestHypertext.g_scientific)
        self.assertEqual(path, 'gallery/heart-crab.html')
        self.assertIn('<title>Heart Crab</title>', html)
        self.assertIn('"nav-pill">Heart<', html)
        self.assertIn('"nav-pill">Crab<', html)
        self.assertNotIn('<em>', html)

    def test_title_scientific_common_name(self):
        """some gallery entries may use scientific names when there isn't a
        common name available
        """
        html, path = hypertext.title(
            ['tubastraea coccinea', 'coral'],
            Where.Gallery,
            TestHypertext.g_scientific,
        )
        self.assertEqual(path, 'gallery/tubastraea-coccinea-coral.html')
        self.assertIn('<title>Tubastraea coccinea Coral</title>', html)
        self.assertIn('"nav-pill"><em>Tubastraea coccinea</em><', html)
        self.assertNotIn('Coccinea', html)

    def test_title_sp_scientific_common_name(self):
        """the taxonomy.yml entry for this name is under sp."""
        html, path = hypertext.title(
            ['pocillopora', 'coral'],
            Where.Gallery,
            TestHypertext.g_scientific,
        )
        self.assertEqual(path, 'gallery/pocillopora-coral.html')
        self.assertIn('<title>Pocillopora Coral</title>', html)
        self.assertIn('"nav-pill"><em>Pocillopora</em><', html)
        self.assertNotIn('Coccinea', html)


class TestTitleTaxonomy(unittest.TestCase):
    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def test_scientific_sp(self):
        html, path = hypertext.title(
            ['Animalia', 'Cnidaria', 'Anthozoa', 'Actiniaria', 'sp.'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertTrue(path.startswith('taxonomy/Animalia-Cnidaria-Anthozoa'), path)
        self.assertTrue(path.endswith('Actiniaria-sp.html'), path)

        self.assertIn('<title>Actiniaria sp.</title>', html)
        self.assertIn('>Anemone<', html)

    def test_translation(self):
        html, title = hypertext.title(
            ['Animalia', 'Arthropoda'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('>Joint-footed Life-possessing-beings<', html)

    def test_translation_deeper(self):
        html, title = hypertext.title(
            ['Animalia', 'Arthropoda', 'Malacostraca'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('>Soft-shelled Joint-footed Life-possessing-beings<', html)

    def test_translation_multi_word_lineage(self):
        html, title = hypertext.title(
            ['Animalia', 'Annelida Polychaeta'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('>Many-bristled Little-ringed Life-possessing-beings<', html)

    def test_translation_duplicates(self):
        """Comb-like Comb-like -> Comb-like"""
        html, title = hypertext.title(
            ['Animalia', 'Mollusca', 'Bivalvia', 'Pectinida', 'Pectinoidea'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('Comb-like Two-valved Soft-bodied Life-possessing-beings', html)

    def test_translation_genus_species(self):
        """skip rest of the lineage when we have genus + species"""
        html, title = hypertext.title(
            ['Decapoda', 'Pacifastacus leniusculus'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('>Lenient Pacific-crawfish<', html)

    def test_translation_species_split(self):
        """look back one level for the genus if necessary"""
        html, title = hypertext.title(
            ['Decapoda', 'Astacidae Pacifastacus', 'leniusculus'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('>Lenient Pacific-crawfish<', html)

    def test_translation_species_extra(self):
        """include the rest of the previous lineage depending on the breaks"""
        html, title = hypertext.title(
            ['Decapoda', 'Astacidae Pacifastacus leniusculus'],
            Where.Taxonomy,
            TestHypertext.t_scientific,
        )
        self.assertIn('>Lenient Pacific-crawfish Lobster<', html)


class TestTitleSites(unittest.TestCase):
    def test_is_dive(self) -> None:
        examples = [
            (True, ['Sund Rock', 'South', 'Shallows 2021-03-06']),
            (True, ['Washington', 'Fort Ward', '2022-12-03']),
            (False, ['Washington', 'Fort Ward']),
            (False, ['Washington']),
        ]
        for expect, lineage in examples:
            title = hypertext.SitesTitle(
                Where.Sites,
                lineage,
                TestHypertext.t_scientific,
            )
            self.assertEqual(title.is_dive(), expect, lineage)

    def test_get_date(self) -> None:
        examples = [
            ('2021-03-06', ['Sund Rock', 'South', 'Shallows 2021-03-06']),
            ('2022-12-03', ['Washington', 'Fort Ward', '2022-12-03']),
        ]
        for date, lineage in examples:
            title = hypertext.SitesTitle(
                Where.Sites,
                lineage,
                TestHypertext.t_scientific,
            )
            self.assertEqual(title.get_date(), date, lineage)


if __name__ == '__main__':
    unittest.main()
