# type: ignore

import unittest

import gallery

from util import collection
from util import database
from util import taxonomy

from util.taxonomy import MappingType
from hypertext import Where


class TestGallery(unittest.TestCase):
    '''gallery.py'''

    g_scientific = taxonomy.mapping()
    t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)

    def setUp(self):
        database.use_test_database()

    def test_find_representative(self):
        '''picking the newest image to represent a tree, or a predefined 'pinned' image'''
        tree = collection.build_image_tree()

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
        tree = collection.build_image_tree()
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


if __name__ == '__main__':
    unittest.main()