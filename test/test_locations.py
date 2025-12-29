import pytest

from diving import locations


class TestLocations:
    """locations.py"""

    def test_site_list(self) -> None:
        """site_list"""
        assert locations.site_list() == (
            'Bonaire, British Columbia, Curacao, Galapagos, Maldives, Roatan, and Washington'
        )

    @pytest.mark.parametrize(
        'site,expected',
        [
            ('Edmonds', 'Washington'),
            ('Oil Slick', 'Bonaire'),
            ('Klein M', 'Bonaire'),
            ('Rockaway Stretch Reef', 'Washington'),
            ('Aquarium', 'British Columbia'),
            ('Agnew', 'British Columbia'),
            ('Captain Island Light', 'British Columbia'),
        ],
    )
    def test_get_region(self, site: str, expected: str) -> None:
        assert locations.get_region(site) == expected

    @pytest.mark.parametrize(
        'site,expected',
        [
            ('Edmonds', None),
            ('Oil Slick', None),
            ('Aquarium', 'Queen Charlotte Strait'),
            ('Agnew', 'Jervis Inlet'),
            ('Captain Island Light', 'Jervis Inlet'),
        ],
    )
    def test_get_subregion(self, site: str, expected: str | None) -> None:
        assert locations.get_subregion(site) == expected

    @pytest.mark.parametrize(
        'before,expected',
        [
            ('Edmonds', 'Washington Edmonds'),
            ('Oil Slick', 'Bonaire Oil Slick'),
            ('Klein M', 'Bonaire Klein M'),
            ('Rockaway Stretch Reef', 'Washington Rockaway Stretch Reef'),
            ('Aquarium', 'British Columbia Queen Charlotte Strait Aquarium'),
            ('Agnew', 'British Columbia Jervis Inlet Agnew'),
            ('Captain Island Light', 'British Columbia Jervis Inlet Captain Island Light'),
        ],
    )
    def test_add_context(self, before: str, expected: str) -> None:
        assert locations.add_context(before) == expected

    @pytest.mark.parametrize(
        'before,expected',
        [
            # Single word regions
            ('Washington', ['Washington']),
            ('Bonaire', ['Bonaire']),
            ('Galapagos', ['Galapagos']),
            # Multi-word region
            ('British Columbia', ['British Columbia']),
            # Region + site
            ('Washington Edmonds', ['Washington', 'Edmonds']),
            ('Washington Fort Ward', ['Washington', 'Fort Ward']),
            ('Bonaire Cliff', ['Bonaire', 'Cliff']),
            # Multi-word region + site
            (
                'British Columbia Jervis Inlet Argonaut Point',
                ['British Columbia', 'Jervis Inlet', 'Argonaut Point'],
            ),
            (
                'British Columbia Queen Charlotte Strait Aquarium',
                ['British Columbia', 'Queen Charlotte Strait', 'Aquarium'],
            ),
            # Sites with multiple words
            ('Washington Sund Rock South Wall', ['Washington', 'Sund Rock', 'South', 'Wall']),
            ('Bonaire Alice in Wonderland', ['Bonaire', 'Alice in Wonderland']),
            ('Roatan Coco View Front Yard', ['Roatan', 'Coco View Front Yard']),
            ("Galapagos Cousin's Rock", ['Galapagos', "Cousin's Rock"]),
            ('Washington Kitsap Memorial Park', ['Washington', 'Kitsap Memorial Park']),
            # With dates
            ('Washington Fort Ward 2020-01-15', ['Washington', 'Fort Ward', '2020-01-15']),
            (
                'British Columbia Jervis Inlet Agnew 2023-09-22',
                ['British Columbia', 'Jervis Inlet', 'Agnew', '2023-09-22'],
            ),
            (
                'British Columbia Queen Charlotte Strait Aquarium 2023-04-02',
                ['British Columbia', 'Queen Charlotte Strait', 'Aquarium', '2023-04-02'],
            ),
            # Sub-region hierarchy
            ('Maldives Ari North', ['Maldives', 'Ari North']),
            ('Maldives Male South', ['Maldives', 'Male South']),
        ],
    )
    def test_where_to_words(self, before: str, expected: list[str]) -> None:
        assert locations.where_to_words(before) == expected

    def test_region_year_ranges(self) -> None:
        ranges = locations._region_year_ranges()

        assert ranges['Galapagos'] == {2021}
        assert ranges['Maldives'] == {2022}
        assert ranges['British Columbia'] == {2020, 2022, 2023, 2024, 2025}

        assert ranges['Bonaire Cliff'] == {2019}
        assert ranges['British Columbia Jervis Inlet'] == {2020, 2022, 2023, 2025}
        assert ranges['British Columbia Queen Charlotte Strait'] == {2023, 2024}
        assert ranges['British Columbia Jervis Inlet Agnew'] == {2023, 2025}
        assert ranges['British Columbia Queen Charlotte Strait Aquarium'] == {2023, 2024}
        assert ranges['Galapagos Fernandina'] == {2021}

    def test_pretty_year_range(self) -> None:
        assert locations._pretty_year_range({1, 3, 4, 6}) == '1, 3-4, 6'
        assert locations._pretty_year_range({1, 2, 3, 4, 5, 6}) == '1-6'
        assert locations._pretty_year_range({1, 6}) == '1, 6'

    def test_region_to_year_range(self) -> None:
        assert locations.find_year_range(['Galapagos']) == '2021'
        assert locations.find_year_range(['Galapagos']) == '2021'
        assert locations.find_year_range(['Maldives']) == '2022'
        assert locations.find_year_range(['British Columbia']) == '2020, 2022-2025'

        assert (
            locations.find_year_range(['British Columbia', 'Jervis Inlet'])
            == '2020, 2022-2023, 2025'
        )
        assert (
            locations.find_year_range(['British Columbia', 'Queen Charlotte Strait']) == '2023-2024'
        )
        assert (
            locations.find_year_range(['British Columbia', 'Jervis Inlet', 'Agnew']) == '2023, 2025'
        )
        assert (
            locations.find_year_range(['British Columbia', 'Queen Charlotte Strait', 'Aquarium'])
            == '2023-2024'
        )
        assert locations.find_year_range(['Galapagos', 'Wolf', 'Shark Bay']) == '2021'
        assert locations.find_year_range(['Galapagos', 'Fernandina']) == '2021'
