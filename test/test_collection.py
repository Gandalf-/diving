import os
from typing import Any, cast

from diving.util import collection, image, static


class TestCollection:
    """collection.py"""

    def test_expand_names(self) -> None:
        """it works"""
        base = image.Image('001 - Fish and Coral.jpg', '2021-11-05 10 Rockaway Beach')
        out = list(collection.expand_names([base]))
        assert len(out) == 2
        fish = out[0]
        coral = out[1]

        assert fish.name == 'Fish'
        assert coral.name == 'Coral'
        assert fish.number == coral.number
        assert fish.directory == coral.directory

    def test_expand_names_noop(self) -> None:
        """it works"""
        base = image.Image('001 - Fish', '2021-11-05 10 Rockaway Beach')
        out = list(collection.expand_names([base]))
        assert len(out) == 1
        fish = out[0]

        assert fish.name == 'Fish'
        assert fish.number == '001'

    def test_position(self) -> None:
        """it works"""
        path = os.path.join(static.image_root, '2023-10-19 3 Sunscape')
        images = collection.delve(path)
        assert len(images) == 9

        first, *_ = images
        *_, last = images
        assert first.position >= 0.0
        assert last.position <= 1.0

        positions = [i.position for i in images]
        assert positions == sorted(positions)

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
        assert 'staghorn coral' in tree
        assert 'fused staghorn coral' in tree

        # They should be siblings (both at same level)
        staghorn_node = tree['staghorn coral']
        fused_node = tree['fused staghorn coral']

        # Neither should have the other as a child
        assert 'fused' not in staghorn_node
        assert 'various' not in staghorn_node
        assert 'data' in staghorn_node
        assert 'data' in fused_node

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
        assert 'hog fish' in tree
        assert 'mexican hog fish' in tree

        # They should be siblings (both at same level)
        hog_node = tree['hog fish']
        mexican_node = tree['mexican hog fish']

        # 'hog' should NOT have a 'mexican' child
        assert 'mexican' not in hog_node
        assert 'data' in hog_node
        assert 'data' in mexican_node

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
        assert 'coral' in tree
        coral_node = tree['coral']

        # Should have 'brain' for specific type and 'various' for general coral
        assert 'brain' in coral_node
        assert 'various' in coral_node

        coral_dict = cast(dict[str, Any], coral_node)
        assert 'data' in coral_dict['brain']
        assert 'data' in coral_dict['various']

    def test_various_to_adult(self) -> None:
        """if the other sibling categories to 'various' are all life cycle, then change various to
        adult"""
        # Create enough images to avoid pruning
        images = [
            image.Image('001 - Juvenile Rockfish.jpg', '2024-01-01 Test'),
            image.Image('002 - Juvenile Rockfish.jpg', '2024-01-01 Test'),
            image.Image('003 - Juvenile Rockfish.jpg', '2024-01-01 Test'),
            image.Image('004 - Rockfish.jpg', '2024-01-01 Test'),
            image.Image('005 - Rockfish.jpg', '2024-01-01 Test'),
            image.Image('006 - Rockfish.jpg', '2024-01-01 Test'),
        ]

        tree = collection._make_tree(images)
        tree = collection.pipeline(tree)

        assert 'rock fish' in tree
        rockfish = tree['rock fish']

        assert 'juvenile' in rockfish
        assert 'adult' in rockfish
