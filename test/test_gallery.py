# type: ignore

import unittest

import gallery
from hypertext import Where
from util import collection, database, taxonomy
from util.image import Image
from util.taxonomy import MappingType


class TestGallery(unittest.TestCase):
    """gallery.py"""

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def setUp(self):
        database.use_test_database()

    def test_find_representative(self):
        """picking the newest image to represent a tree, or a predefined 'pinned' image"""
        tree = collection.build_image_tree()

        self.assertIn('barnacle', tree)
        out = gallery.find_representative(tree['barnacle'], Where.Gallery, lineage=['barnacle'])
        self.assertIsNotNone(out)

    def test_find_representative_skips_videos(self) -> None:
        tree = {
            'fish': [
                Image('001 - Blue Fish.mov', '2023-01-01 Rockaway Beach'),
                Image('002 - Fast Fish.mov', '2023-01-01 Rockaway Beach'),
                Image('003 - Gray Fish.jpg', '2020-01-01 Rockaway Beach'),
            ]
        }
        out = gallery.find_representative(tree, Where.Gallery, lineage=['fish'])
        self.assertEqual(out.name, 'Gray Fish')

    def test_find_representative_sites(self) -> None:
        tree = {
            'Rockaway Beach': [
                Image('001 - Blue Fish.jpg', '2023-01-01 Rockaway Beach'),
                Image('002 - Fast Fish.jpg', '2023-01-01 Rockaway Beach'),
                Image('003 - Gray Fish.jpg', '2020-01-01 Rockaway Beach'),
            ]
        }
        out = gallery.find_representative(tree, Where.Sites)
        self.assertEqual(out.name, 'Fast Fish')

    def test_find_representative_prefers_single_subject(self) -> None:
        """find_representative should prefer images without multiple subjects"""
        # Gallery/Taxonomy: prefers newest single-subject image
        tree = {
            'fish': [
                Image('001 - Shark and Remora.jpg', '2024-01-01 Rockaway Beach'),
                Image('002 - Fish with Kelp.jpg', '2023-06-01 Rockaway Beach'),
                Image('003 - Blue Fish.jpg', '2023-01-01 Rockaway Beach'),
                Image('004 - Red Fish.jpg', '2020-01-01 Rockaway Beach'),
            ]
        }
        out = gallery.find_representative(tree, Where.Gallery)
        self.assertEqual(out.name, 'Blue Fish')

        # Sites: prefers middle single-subject image
        tree_sites = {
            'Rockaway Beach': [
                Image('001 - Shark and Remora.jpg', '2024-01-01 Rockaway Beach'),
                Image('002 - Blue Fish.jpg', '2023-06-01 Rockaway Beach'),
                Image('003 - Red Fish.jpg', '2023-01-01 Rockaway Beach'),
                Image('004 - Fish with Kelp.jpg', '2020-01-01 Rockaway Beach'),
            ]
        }
        out = gallery.find_representative(tree_sites, Where.Sites)
        # Middle of single-subject images [Blue Fish, Red Fish] is Blue Fish (index 0 of 2)
        self.assertIn(out.name, ['Blue Fish', 'Red Fish'])

    def test_find_representative_only_multiple_subjects(self) -> None:
        """when only multi-subject images available, still pick one"""
        tree = {
            'fish': [
                Image('001 - Shark and Remora.jpg', '2023-01-01 Rockaway Beach'),
                Image('002 - Fish with Kelp.jpg', '2020-01-01 Rockaway Beach'),
            ]
        }
        out = gallery.find_representative(tree, Where.Gallery)
        self.assertEqual(out.name, 'Shark and Remora')

    def test_key_to_subject_gallery(self):
        """current element to visible text"""

        def key_to_subject(key):
            return gallery._key_to_subject(key, Where.Gallery)

        self.assertEqual(key_to_subject('fancy fish'), 'Fancy Fish')
        self.assertEqual(key_to_subject('octopus'), '<em>Octopus</em>')

    def test_key_to_subject_taxonomy(self):
        """current element to visible text"""

        def key_to_subject(key):
            return gallery._key_to_subject(key, Where.Taxonomy)

        self.assertEqual(key_to_subject('octopoda octopus'), 'O. octopus')

    def test_key_to_subject_sites(self):
        """current element to visible text"""

        def key_to_subject(key):
            return gallery._key_to_subject(key, Where.Sites)

        self.assertEqual(key_to_subject('Stretch Reef'), 'Stretch Reef')
        self.assertEqual(key_to_subject('Shallows 2021-03-06'), 'Shallows')
        self.assertEqual(key_to_subject('2021-03-06'), 'March 6th, 2021')

    def test_html_tree_gallery(self):
        """basics"""
        tree = collection.build_image_tree()
        sub_tree = tree['coral']
        htmls = gallery.html_tree(sub_tree, Where.Gallery, TestGallery.g_scientific, ['coral'])

        self.assertNotEqual(htmls, [])
        (path, html) = htmls[-1]

        self.assertEqual(path, 'gallery/coral.html')
        self.assertRegex(html, r'(?s)<head>.*<title>.*Coral.*</title>.*</head>')
        self.assertRegex(html, r'(?s)<h3.*Fan.*</h3>')
        self.assertRegex(html, r'(?s)<h3.*Rhizopsammia wellingtoni.*</h3>')


if __name__ == '__main__':
    unittest.main()
