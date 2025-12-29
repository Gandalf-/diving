import pytest

from diving.util import image


class TestImage:
    """image.py"""

    def test_egg_reorder(self) -> None:
        """reinterpret fish eggs as eggs fish"""
        img = image.Image('001 - Fish Eggs.jpg', '2020-01-01 Rockaway Beach')
        assert img.name == 'Eggs Fish'

    @pytest.mark.parametrize(
        'before,after',
        [
            ('prawn', 'prawn shrimp'),
            ('french grunt', 'french grunt fish'),
            ('kelp greenling', 'kelp greenling fish'),
            ('giant pacific octopus', 'giant pacific octopus'),
            ('noble sea lemon', 'noble sea lemon nudibranch'),
            ('brain coral', 'brain coral'),
        ],
    )
    def test_categorize(self, before: str, after: str) -> None:
        """subjects are recategorized, but that needs to be undone for some presentations"""
        assert image.categorize(before) == after
        assert image.uncategorize(after) == before

    @pytest.mark.parametrize(
        'before,after',
        [
            ('adult male kelp greenling', 'kelp greenling'),
            ('giant pacific octopus', 'giant pacific octopus'),
        ],
    )
    def test_unqualify(self, before: str, after: str) -> None:
        """remove qualifiers"""
        assert image.unqualify(before) == after

    @pytest.mark.parametrize(
        'before,after',
        [
            ('copper rockfish', 'copper rock fish'),
            ('eagleray', 'eagle ray'),
            ('six rayed star', 'six rayed star'),
            ('giant pacific octopus', 'giant pacific octopus'),
        ],
    )
    def test_split(self, before: str, after: str) -> None:
        """some names are broken to categorize them"""
        split = image.split(before)
        assert split == after
        assert image.unsplit(split) == before

    @pytest.mark.parametrize(
        'directory,expected',
        [
            ('2021-11-05 Rockaway Beach', '2021-11-05 Rockaway Beach'),
            ('2021-11-05 1 Rockaway Beach', '2021-11-05 Rockaway Beach'),
            ('2021-11-05 10 Rockaway Beach', '2021-11-05 Rockaway Beach'),
        ],
    )
    def test_image_location(self, directory: str, expected: str) -> None:
        """names can have a number after the date to force ordering"""
        picture = image.Image('fish', directory)
        assert picture.location() == expected

    @pytest.mark.parametrize(
        'directory,expected',
        [
            ('2021-11-05 Rockaway Beach', 'Rockaway Beach'),
            ('2021-11-05 1 Rockaway Beach', 'Rockaway Beach'),
            ('2021-11-05 10 Rockaway Beach', 'Rockaway Beach'),
        ],
    )
    def test_image_site(self, directory: str, expected: str) -> None:
        picture = image.Image('fish', directory)
        assert picture.site() == expected

    @pytest.mark.parametrize(
        'filename,expected',
        [
            ('001 - Sea Lemon.jpg', 'sea lemon'),
            ('001 - Clams.jpg', 'clam'),
            ('001 - Decorator Crabs.jpg', 'decorator crab'),
            ('001 - Green Algae.jpg', 'green algae'),
            ('001 - Octopus.jpg', 'octopus'),
            ('001 - Grass.jpg', 'grass'),
            ('001 - Painted Chitons.jpg', 'painted chiton'),
        ],
    )
    def test_image_singular(self, filename: str, expected: str) -> None:
        picture = image.Image(filename, '2020-01-01 Rockaway Beach')
        assert picture.singular() == expected

    @pytest.mark.parametrize(
        'filename,expected',
        [
            ('001 - Clams.jpg', 'clam'),
            ('001 - Juvenile Decorator Crab.jpg', 'decorator crab'),
            ('001 - Green Algae.jpg', 'green algae'),
            ('001 - Octopus Eggs.jpg', 'eggs octopus'),
            ('001 - Various Grass.jpg', 'grass'),
            ('001 - Painted Chitons.jpg', 'painted chiton'),
            ('001 - Kelp Greenling Eggs.jpg', 'eggs kelp greenling'),
        ],
    )
    def test_image_simplified(self, filename: str, expected: str) -> None:
        picture = image.Image(filename, '2020-01-01 Rockaway Beach')
        assert picture.simplified() == expected

    def test_image_basics(self) -> None:
        img = image.Image('001 - Clams.jpg', '2020-01-01 Rockaway Beach')
        assert img.name == 'Clams'
        assert img.number == '001'
        assert img.directory == '2020-01-01 Rockaway Beach'
        assert img.is_image is True
        assert img.is_video is False
        assert img.thumbnail() == '/imgs/test.webp'
        assert img.fullsize() == '/full/test.webp'

    def test_video_basics(self) -> None:
        img = image.Image('001 - Clams.mov', '2020-01-01 Rockaway Beach')
        assert img.name == 'Clams'
        assert img.number == '001'
        assert img.directory == '2020-01-01 Rockaway Beach'
        assert img.is_image is False
        assert img.is_video is True
        assert img.thumbnail() == '/clips/test.mp4'
        assert img.fullsize() == '/video/test.mp4'

    @pytest.mark.parametrize(
        'filename,expected',
        [
            ('001 - Shark and Remora.jpg', True),
            ('001 - Crab with Anemone.jpg', True),
            ('001 - Fish and Kelp.jpg', True),
            ('001 - Giant Pacific Octopus.jpg', False),
            ('001 - Painted Chiton.jpg', False),
            ('001.jpg', False),
        ],
    )
    def test_has_multiple_subjects(self, filename: str, expected: bool) -> None:
        """check if image name contains multiple subjects"""
        from diving.util.collection import expand_names

        img = image.Image(filename, '2020-01-01 Rockaway Beach')
        assert img.has_multiple_subjects() == expected, f'Failed for {filename}'

        # Also test after expand_names processes it
        expanded = list(expand_names([img]))
        for expanded_img in expanded:
            assert (
                expanded_img.has_multiple_subjects() == expected
            ), f'Failed for {filename} after expand_names'

    def test_depth_at_beyond_range(self) -> None:
        """_depth_at should handle position beyond all depth measurements"""
        depths = [(0.0, 0), (0.5, 30), (0.8, 50)]

        # Position beyond all measurements should return last depth (50)
        result = image._depth_at(depths, 1.0)
        assert result == 50

        # Also test with position slightly beyond
        result = image._depth_at(depths, 0.95)
        assert result == 50
