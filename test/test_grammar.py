import pytest

from diving.util import grammar


@pytest.mark.parametrize(
    'plural,expected',
    [
        ('Kelp Greenling', 'kelp greenling'),
        ('Kelp Greenlings', 'kelp greenling'),
    ],
)
def test_singular(plural: str, expected: str) -> None:
    assert grammar.singular(plural) == expected


@pytest.mark.parametrize(
    'singular,expected',
    [
        ('Algae', 'Algae'),
        ('Kelp Greenling', 'Kelp Greenlings'),
        ('Algae Eelgrass', 'Algae Eelgrass'),
        ('Red Rock Crab', 'Red Rock Crabs'),
        ('Galapagos Octopus', 'Galapagos Octopus'),
        ("Heath's Dorid", "Heath's Dorids"),
        ('Giant Nudibranch', 'Giant Nudibranchs'),
        ('Feather Duster Worm', 'Feather Duster Worms'),
        ('Reef Manta Ray', 'Reef Manta Rays'),
        ('Fish Egg', 'Fish Eggs'),
        ('Encrusting Bryozoan', 'Encrusting Bryozoans'),
    ],
)
def test_pluralize(singular: str, expected: str) -> None:
    assert grammar.plural(singular) == expected
