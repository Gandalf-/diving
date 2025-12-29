import pytest

from diving import information


@pytest.mark.parametrize(
    'lineage,expected',
    [
        ([], []),
        (['Animalia'], ['Animalia']),
        (['Animalia', 'Mollusca', 'Gastropoda'], ['Gastropoda']),
        # split intermediate stuff
        (
            ['Gastropoda', 'Dendronotoidea Dendronotidae Dendronotus'],
            ['Dendronotoidea', 'Dendronotidae', 'Dendronotus'],
        ),
        # genus and species split
        (
            ['Gastropoda', 'Dendronotoidea Dendronotidae Dendronotus', 'rufus'],
            ['Dendronotus rufus'],
        ),
        # genus and species together
        (
            ['Cancroidea Cancridae', 'Glebocarcinus oregonesis'],
            ['Glebocarcinus oregonesis'],
        ),
        # genus and species together with extra
        (
            ['Pleurobranchoidea', 'Pleurobranchidae Berthella californica'],
            ['Pleurobranchidae', 'Berthella californica'],
        ),
    ],
)
def test_lineage_to_names(lineage: list[str], expected: list[str]) -> None:
    """extract the right parts for look up"""
    parts = information.lineage_to_names(lineage)
    assert parts == expected
