import unittest

import util.translator as translator


class TestTranslator(unittest.TestCase):
    def setUp(self) -> None:
        self.table = translator.parse_table()
        self.index = translator.to_index(self.table)

    def translate(self, word: str) -> str:
        # return translator.translate(self.index, word)
        return translator.convert(word)

    def test_is_lang(self) -> None:
        self.assertTrue(translator.is_lang('L Latin'))
        self.assertTrue(translator.is_lang('L, G'))
        self.assertTrue(translator.is_lang('G'))
        self.assertTrue(translator.is_lang('L'))
        self.assertTrue(translator.is_lang('G blah'))

    def test_table_parsing(self) -> None:
        self.assertTrue(len(self.table) > 0)

        known = ('thorny, spiny', 'stemless', 'ray, radial', 'sharpened, pointed')
        for i, known in enumerate(known):
            entry = self.table[i]
            self.assertEqual(known, entry.english, entry)

        for entry in self.table:
            self.assertEqual(len(entry), 5)
            self.assertTrue(translator.is_lang(entry.lang), entry)
            self.assertNotIn('All pages with titles', entry.roots)

            self.assertFalse(translator.is_lang(entry.latin), entry)
            self.assertFalse(translator.is_lang(entry.english), entry)
            self.assertFalse(translator.is_lang(entry.example), entry)
            self.assertFalse(translator.is_lang(entry.roots), entry)

    def test_get_roots(self) -> None:
        example = 'ventralis – ventrale ventralis'
        self.assertEqual(example.replace('–', ''), 'ventralis  ventrale ventralis')

        self.assertEqual(
            translator.get_roots(self.table[0]),
            {'acanthus', 'acanthias', 'acantha', 'acanthium'},
        )
        self.assertEqual(
            translator.get_roots(self.table[12]),
            {'albiceps'},
        )

    def test_to_index(self) -> None:
        self.assertTrue(len(self.index) > 0)

        for key in self.index:
            self.assertTrue(key.islower(), key)
            self.assertNotIn(' ', key)

        self.assertEqual(self.index['aculeatum'], 'prickly')
        self.assertEqual(self.index['agrestis'], 'of the field')
        self.assertEqual(self.index['cephal'], 'head')

        self.assertEqual(self.index['lineatus'], 'lined or striped')
        self.assertEqual(self.index['olearis'], 'oil')

    def test_translate_exact(self) -> None:
        self.assertEqual(self.translate('giganteus'), 'giant')
        self.assertEqual(self.translate('versicolor'), 'many-colored')

    def test_prefix(self) -> None:
        self.assertEqual(self.translate('hyperiidae'), 'over-iidae')

    def test_translate_prefix_suffix(self) -> None:
        self.assertEqual(self.translate('cephalopod'), 'head-foot')
        self.assertEqual(self.translate('gastropod'), 'stomach-foot')
        self.assertEqual(self.translate('solaster'), 'sun-star')
        self.assertEqual(self.translate('asteroidea'), 'star-shaped')

    def test_translate_suffix_post(self) -> None:
        self.assertEqual(self.translate('decapoda'), 'ten-footed')
        self.assertEqual(self.translate('pantopoda'), 'all-footed')
        self.assertEqual(self.translate('nudibranchia'), 'naked-gills')


if __name__ == '__main__':
    unittest.main()
