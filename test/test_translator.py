import unittest

from util.translator import translate, cleanup


class TestTranslator(unittest.TestCase):
    def test_load_yaml(self) -> None:
        self.assertEqual(translate('unguiculata'), 'Clawed')
        self.assertEqual(translate('acarnidae'), 'Pointless family')
        self.assertIsNone(translate('nothing'))

    def test_cleanup(self) -> None:
        self.assertEqual(cleanup('pilosa', 'Hairy'), 'Hairy')
        self.assertEqual(cleanup('polychaeta', 'Many bristled'), 'Many-bristled')
        self.assertIsNone(cleanup('parasabella', 'Parasabella'))


if __name__ == '__main__':
    unittest.main()
