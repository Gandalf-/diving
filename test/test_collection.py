import os
import unittest

from util import collection, database, image, static


class TestCollection(unittest.TestCase):
    """collection.py"""

    def setUp(self) -> None:
        database.use_test_database()

    def test_expand_names(self) -> None:
        """it works"""
        base = image.Image('001 - Fish and Coral.jpg', '2021-11-05 10 Rockaway Beach')
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 2)
        fish = out[0]
        coral = out[1]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(coral.name, 'Coral')
        self.assertEqual(fish.number, coral.number)
        self.assertEqual(fish.directory, coral.directory)

    def test_expand_names_noop(self) -> None:
        """it works"""
        base = image.Image('001 - Fish', '2021-11-05 10 Rockaway Beach')
        out = list(collection.expand_names([base]))
        self.assertEqual(len(out), 1)
        fish = out[0]

        self.assertEqual(fish.name, 'Fish')
        self.assertEqual(fish.number, '001')

    def test_position(self) -> None:
        """it works"""
        path = os.path.join(static.image_root, '2023-10-19 3 Sunscape')
        images = collection.delve(path)
        self.assertEqual(len(images), 9)

        first, *_ = images
        *_, last = images
        self.assertGreaterEqual(first.position, 0.0)
        self.assertLessEqual(last.position, 1.0)

        positions = [i.position for i in images]
        self.assertEqual(positions, sorted(positions))

    def test_unnest_staghorn_coral(self) -> None:
        """staghorn coral and fused staghorn coral should be siblings after pipeline"""
        # Create enough images to avoid pruning (need > 5)
        images = [
            image.Image('001 - Staghorn Coral.jpg', '2024-01-01 Test'),
            image.Image('002 - Staghorn Coral.jpg', '2024-01-01 Test'),
            image.Image('003 - Staghorn Coral.jpg', '2024-01-01 Test'),
            image.Image('004 - Fused Staghorn Coral.jpg', '2024-01-01 Test'),
            image.Image('005 - Fused Staghorn Coral.jpg', '2024-01-01 Test'),
            image.Image('006 - Fused Staghorn Coral.jpg', '2024-01-01 Test'),
        ]

        # Build tree and run through full pipeline
        tree = collection._make_tree(images)
        tree = collection.pipeline(tree)

        # Check structure after pipeline
        # After compress, keys get merged so we expect top-level keys
        self.assertIn('staghorn coral', tree)
        self.assertIn('fused staghorn coral', tree)

        # They should be siblings (both at same level)
        staghorn_node = tree['staghorn coral']
        fused_node = tree['fused staghorn coral']

        # Neither should have the other as a child
        self.assertNotIn('fused', staghorn_node)
        self.assertNotIn('various', staghorn_node)
        self.assertIn('data', staghorn_node)
        self.assertIn('data', fused_node)

    def test_unnest_hogfish(self) -> None:
        """hogfish and mexican hogfish should be siblings after pipeline"""
        # Create enough images to avoid pruning
        images = [
            image.Image('001 - Hogfish.jpg', '2024-01-01 Test'),
            image.Image('002 - Hogfish.jpg', '2024-01-01 Test'),
            image.Image('003 - Hogfish.jpg', '2024-01-01 Test'),
            image.Image('004 - Mexican Hogfish.jpg', '2024-01-01 Test'),
            image.Image('005 - Mexican Hogfish.jpg', '2024-01-01 Test'),
            image.Image('006 - Mexican Hogfish.jpg', '2024-01-01 Test'),
        ]

        tree = collection._make_tree(images)
        tree = collection.pipeline(tree)

        # After compress, keys get merged
        self.assertIn('hog fish', tree)
        self.assertIn('mexican hog fish', tree)

        # They should be siblings (both at same level)
        hog_node = tree['hog fish']
        mexican_node = tree['mexican hog fish']

        # 'hog' should NOT have a 'mexican' child
        self.assertNotIn('mexican', hog_node)
        self.assertIn('data', hog_node)
        self.assertIn('data', mexican_node)

    def test_normal_nesting_with_various(self) -> None:
        """non-complete species should still create 'various' normally"""
        # Create enough images to avoid pruning
        images = [
            image.Image('001 - Coral.jpg', '2024-01-01 Test'),
            image.Image('002 - Coral.jpg', '2024-01-01 Test'),
            image.Image('003 - Coral.jpg', '2024-01-01 Test'),
            image.Image('004 - Brain Coral.jpg', '2024-01-01 Test'),
            image.Image('005 - Brain Coral.jpg', '2024-01-01 Test'),
            image.Image('006 - Brain Coral.jpg', '2024-01-01 Test'),
        ]

        tree = collection._make_tree(images)
        tree = collection.pipeline(tree)

        # 'coral' by itself is not a complete species (it's too general)
        # So normal nesting occurs: coral -> {brain: {...}, various: {...}}
        self.assertIn('coral', tree)
        coral_node = tree['coral']

        # Should have 'brain' for specific type and 'various' for general coral
        self.assertIn('brain', coral_node)
        self.assertIn('various', coral_node)

        # Verify data is in both (need to cast to dict for type checker)
        from typing import Any, Dict, cast

        coral_dict = cast(Dict[str, Any], coral_node)
        self.assertIn('data', coral_dict['brain'])
        self.assertIn('data', coral_dict['various'])

    def test_qualified_variants_not_unbundled(self) -> None:
        """qualified variants of same species should nest with 'various', not unbundle"""
        # 'mating' and 'juvenile' are qualifiers that get removed by simplified()
        # Both simplify to 'mottled star', so they should NOT be unbundled
        images = [
            image.Image('001 - Mottled Star.jpg', '2024-01-01 Test'),
            image.Image('002 - Mottled Star.jpg', '2024-01-01 Test'),
            image.Image('003 - Mottled Star.jpg', '2024-01-01 Test'),
            image.Image('004 - Mating Mottled Star.jpg', '2024-01-01 Test'),
            image.Image('005 - Mating Mottled Star.jpg', '2024-01-01 Test'),
            image.Image('006 - Juvenile Mottled Star.jpg', '2024-01-01 Test'),
        ]

        tree = collection._make_tree(images)
        tree = collection.pipeline(tree)

        # After compress, should have 'mottled star' at top level
        self.assertIn('mottled star', tree)
        mottled_node = tree['mottled star']

        # Should have 'various' for unqualified mottled star
        # and nested qualified variants (mating, juvenile)
        self.assertIn('various', mottled_node)

        # Should NOT have been unbundled to separate top-level keys
        self.assertNotIn('mating mottled star', tree)
        self.assertNotIn('juvenile mottled star', tree)


if __name__ == '__main__':
    unittest.main()
