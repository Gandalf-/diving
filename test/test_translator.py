import unittest

from util.translator import lookup, cleanup


class TestTranslator(unittest.TestCase):
    def test_load_yaml(self) -> None:
        self.assertEqual(lookup('unguiculata'), 'Clawed')
        self.assertIsNone(lookup('nothing'))

    def test_cleanup(self) -> None:
        self.assertEqual(cleanup('polychaeta', 'Many bristles'), 'Many bristles')
        self.assertIsNone(cleanup('parasabella', 'Parasabella'))


if __name__ == '__main__':
    unittest.main()
