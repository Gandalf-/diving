import pytest

from diving import hypertext
from diving.hypertext import Side, Where
from diving.util import taxonomy
from diving.util.taxonomy import MappingType

g_scientific = taxonomy.mapping()
t_scientific = taxonomy.mapping(where=MappingType.Taxonomy)


class TestHypertext:
    """hypertext.py"""

    @pytest.mark.parametrize(
        'name,description',
        [
            ('Maldives', 'Maldives, organized by dive site and date'),
            ('British Columbia', 'British Columbia, organized by dive site and date'),
            (
                'British Columbia Aquarium 2023-04-02',
                'Aquarium, British Columbia on April 2nd, 2023',
            ),
            (
                'Washington Rockaway Stretch Reef 2021-11-20',
                'Rockaway Stretch Reef, Washington on November 20th, 2021',
            ),
            ('Galapagos Fernandina', 'Fernandina, Galapagos, organized by dive site and date'),
            (
                'Galapagos Isabella Punta Vicente Roca 2021-08-28',
                'Isabella Punta Vicente Roca, Galapagos on August 28th, 2021',
            ),
            ('Bonaire Klein M', 'Klein M, Bonaire, organized by dive site and date'),
            (
                'Bonaire One Thousand Steps 2021-07-04',
                'One Thousand Steps, Bonaire on July 4th, 2021',
            ),
        ],
    )
    def test_description_sites(self, name: str, description: str) -> None:
        expect = f'Explore high quality scuba diving pictures from {description}.'
        assert hypertext.description(name, Where.Sites) == expect

    @pytest.mark.parametrize(
        'name,description',
        [
            ('Red Rock Crab', 'Red Rock Crabs'),
            ("Heath's Dorid Nudibranch", "Heath's Dorid Nudibranchs"),
            ('Various Red Octopus', 'Red Octopus'),
            ('Tubastraea coccinea Coral', 'Tubastraea coccinea Corals'),
        ],
    )
    def test_description_gallery(self, name: str, description: str) -> None:
        expect = (
            f'Explore high quality scuba diving pictures of {description} and related organisms.'
        )
        assert hypertext.description(name, Where.Gallery) == expect

    @pytest.mark.parametrize(
        'name,description',
        [
            ('Animalia', 'members of Animalia'),
            ('Malacostraca Decapoda', 'members of Malacostraca Decapoda'),
            ('Alpheoidea Alpheidae Alpheus djeddensis', 'Alpheus djeddensis and related organisms'),
            ('Cancer antennarius', 'Cancer antennarius and related organisms'),
        ],
    )
    def test_description_taxonomy(self, name: str, description: str) -> None:
        expect = f'Explore high quality scuba diving pictures of {description}.'
        assert hypertext.description(name, Where.Taxonomy) == expect

    @pytest.mark.parametrize(
        'key,right_side,lineage,expected',
        [
            (None, False, ['a', 'b', 'c'], 'a-b-c'),
            (None, True, ['a', 'b', 'c'], 'a-b-c'),
            ('d', False, ['a', 'b', 'c'], 'd-a-b-c'),
            ('d', True, ['a', 'b', 'c'], 'a-b-c-d'),
        ],
    )
    def test_lineage_to_link(
        self, key: str | None, right_side: bool, lineage: list[str], expected: str
    ) -> None:
        """converting lineage to links between sites"""
        side = Side.Right if right_side else Side.Left
        link = hypertext.lineage_to_link(lineage, side, key)
        assert link == expected

    def test_title_names(self) -> None:
        """html titles top level"""
        # gallery
        html, path = hypertext.title([], Where.Gallery, g_scientific)
        assert path == 'gallery/index.html'
        assert '<title>Gallery</title>' in html

        # taxonomy
        html, path = hypertext.title([], Where.Taxonomy, t_scientific)
        assert path == 'taxonomy/index.html'
        assert '<title>Taxonomy</title>' in html

    def test_switcher_button(self) -> None:
        """See that the correct HTML is generated for each site's button"""
        for where in Where:
            shorter = hypertext.switcher_button(where)
            assert f'href="/{where.name.lower()}/"' in shorter
            assert where.name not in shorter

            longer = hypertext.switcher_button(where, long=True)
            assert f'href="/{where.name.lower()}/"' in longer
            assert where.name in longer

    def test_top_timeline_spacing(self) -> None:
        html, title = hypertext.title([], Where.Timeline, g_scientific)
        assert 'scientific' not in html

    def test_top_gallery_search_bar(self) -> None:
        html, title = hypertext.title([], Where.Gallery, g_scientific)
        assert 'input type="text"' in html


class TestTitleGallery:
    def test_title_ordinary(self) -> None:
        """typical common name"""
        html, path = hypertext.title(['heart', 'crab'], Where.Gallery, g_scientific)
        assert path == 'gallery/heart-crab.html'
        assert '<title>Heart Crab</title>' in html
        assert '"nav-pill">Heart<' in html
        assert '"nav-pill">Crab<' in html
        assert '<em>' not in html

    def test_title_scientific_common_name(self) -> None:
        """some gallery entries may use scientific names when there isn't a common name"""
        html, path = hypertext.title(['tubastraea coccinea', 'coral'], Where.Gallery, g_scientific)
        assert path == 'gallery/tubastraea-coccinea-coral.html'
        assert '<title>Tubastraea coccinea Coral</title>' in html
        assert '"nav-pill"><em>Tubastraea coccinea</em><' in html
        assert 'Coccinea' not in html

    def test_title_sp_scientific_common_name(self) -> None:
        """the taxonomy.yml entry for this name is under sp."""
        html, path = hypertext.title(['pocillopora', 'coral'], Where.Gallery, g_scientific)
        assert path == 'gallery/pocillopora-coral.html'
        assert '<title>Pocillopora Coral</title>' in html
        assert '"nav-pill"><em>Pocillopora</em><' in html
        assert 'Coccinea' not in html


class TestTitleTaxonomy:
    def test_scientific_sp(self) -> None:
        html, path = hypertext.title(
            ['Animalia', 'Cnidaria', 'Anthozoa', 'Actiniaria', 'sp.'],
            Where.Taxonomy,
            t_scientific,
        )
        assert path.startswith('taxonomy/Animalia-Cnidaria-Anthozoa'), path
        assert path.endswith('Actiniaria-sp.html'), path
        assert '<title>Actiniaria sp.</title>' in html
        assert '>Anemone<' in html

    def test_translation(self) -> None:
        html, title = hypertext.title(['Animalia', 'Arthropoda'], Where.Taxonomy, t_scientific)
        assert '>Joint-footed Life-possessing-beings<' in html

    def test_translation_deeper(self) -> None:
        html, title = hypertext.title(
            ['Animalia', 'Arthropoda', 'Malacostraca'], Where.Taxonomy, t_scientific
        )
        assert '>Soft-shelled Joint-footed Life-possessing-beings<' in html

    def test_translation_multi_word_lineage(self) -> None:
        html, title = hypertext.title(
            ['Animalia', 'Annelida Polychaeta'], Where.Taxonomy, t_scientific
        )
        assert '>Many-bristled Little-ringed Life-possessing-beings<' in html

    def test_translation_duplicates(self) -> None:
        """Comb-like Comb-like -> Comb-like"""
        html, title = hypertext.title(
            ['Animalia', 'Mollusca', 'Bivalvia', 'Pectinida', 'Pectinoidea'],
            Where.Taxonomy,
            t_scientific,
        )
        assert 'Comb-like Two-valved Soft-bodied Life-possessing-beings' in html

    def test_translation_genus_species(self) -> None:
        """skip rest of the lineage when we have genus + species"""
        html, title = hypertext.title(
            ['Decapoda', 'Pacifastacus leniusculus'], Where.Taxonomy, t_scientific
        )
        assert '>Lenient Pacific-crawfish<' in html

    def test_translation_species_split(self) -> None:
        """look back one level for the genus if necessary"""
        html, title = hypertext.title(
            ['Decapoda', 'Astacidae Pacifastacus', 'leniusculus'], Where.Taxonomy, t_scientific
        )
        assert '>Lenient Pacific-crawfish<' in html

    def test_translation_species_extra(self) -> None:
        """include the rest of the previous lineage depending on the breaks"""
        html, title = hypertext.title(
            ['Decapoda', 'Astacidae Pacifastacus leniusculus'], Where.Taxonomy, t_scientific
        )
        assert '>Lenient Pacific-crawfish Lobster<' in html


class TestTitleSites:
    @pytest.mark.parametrize(
        'expected,lineage',
        [
            (True, ['Sund Rock', 'South', 'Shallows 2021-03-06']),
            (True, ['Washington', 'Fort Ward', '2022-12-03']),
            (False, ['Washington', 'Fort Ward']),
            (False, ['Washington']),
        ],
    )
    def test_is_dive(self, expected: bool, lineage: list[str]) -> None:
        title = hypertext.SitesTitle(Where.Sites, lineage, t_scientific)
        assert title.is_dive() == expected

    @pytest.mark.parametrize(
        'expected,lineage',
        [
            ('2021-03-06', ['Sund Rock', 'South', 'Shallows 2021-03-06']),
            ('2022-12-03', ['Washington', 'Fort Ward', '2022-12-03']),
        ],
    )
    def test_get_date(self, expected: str, lineage: list[str]) -> None:
        title = hypertext.SitesTitle(Where.Sites, lineage, t_scientific)
        assert title.get_date() == expected
