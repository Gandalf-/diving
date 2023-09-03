import unittest

from util import grammar


class TestGrammar(unittest.TestCase):
    def test_pluralize(self) -> None:
        pairs = [
            ('Algae', 'Algae'),
            ('Algae Eelgrass', 'Algae Eelgrass'),
            ('Red Rock Crab', 'Red Rock Crabs'),
            ('Galapagos Octopus', 'Galapagos Octopus'),
            ('Heath\'s Dorid', 'Heath\'s Dorids'),
            ('Giant Nudibranch', 'Giant Nudibranchs'),
            ('Feather Duster Worm', 'Feather Duster Worms'),
            ('Reef Manta Ray', 'Reef Manta Rays'),
            ('Fish Egg', 'Fish Eggs'),
            ('Encrusting Bryozoan', 'Encrusting Bryozoans'),
        ]
        for singular, plural in pairs:
            self.assertEqual(grammar.plural(singular), plural)


if __name__ == '__main__':
    unittest.main()
