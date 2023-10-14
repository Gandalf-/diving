import unittest

from util.translator import cleanup, translate


class TestTranslator(unittest.TestCase):
    def test_load_yaml(self) -> None:
        self.assertEqual(translate('unguiculata'), 'Small-clawed')
        self.assertEqual(translate('acarnidae'), 'Pointless')

    def test_cleanup(self) -> None:
        self.assertEqual(cleanup('pilosa', 'Hairy'), 'Hairy')
        self.assertEqual(cleanup('polychaeta', 'Many bristled'), 'Many-bristled')


if __name__ == '__main__':
    unittest.main()
