# type: ignore

import unittest

from util import collection
from util import verify
from util import database


class TestVerify(unittest.TestCase):
    '''verify.py'''

    def setUp(self) -> None:
        database.use_test_database()

    def _build_swapped_tree(self) -> collection.ImageTree:
        '''swapped words'''
        tree = collection.build_image_tree()
        nudi = tree['nudibranch']['sea lemon']['freckled pale']['data'].pop()
        nudi.name = 'Pale Freckled Sea Lemon'

        tree['nudibranch']['sea lemon']['pale freckled'] = {'data': [nudi]}

        self.assertIn('pale freckled', tree['nudibranch']['sea lemon'].keys())
        self.assertIn('freckled pale', tree['nudibranch']['sea lemon'].keys())

        return tree

    def test_detect_wrong_name_order(self) -> None:
        '''pale freckled sea lemon vs freckled pale sea lemon'''
        tree = self._build_swapped_tree()
        wrong = list(verify._find_wrong_name_order(tree))
        self.assertEqual(wrong, [('freckled pale', 'pale freckled')])

    def test_detect_misspelling(self) -> None:
        '''curlyhead spaghetti worm vs curlyheaded spaghetti worm'''
        examples = [
            ['curlyhead spaghetti worm', 'curlyheaded spaghetti worm'],
            ['encrusting bryozoan', 'encrusting byrozoan'],
            ['nanaimo nudibranch', 'naniamo nudibranch'],
        ]
        for names in examples:
            wrong = [sorted(w) for w in verify._possible_misspellings(names[:])]
            self.assertEqual(wrong, [names])

    def test_detect_misspelling_ignore_explicit(self) -> None:
        '''don't consider ignored names'''
        examples = [
            ['submerged log', 'submerged wood'],
            ['a unknown', 'b unknown'],
        ]
        for names in examples:
            wrong = [sorted(w) for w in verify._possible_misspellings(names[:])]
            self.assertEqual(wrong, [])

    def test_detect_misspelling_ignore_scientific(self) -> None:
        '''a name isn't misspelled if it has a scientific name'''
        examples = [
            ['dalls dendronotid nudibranch', 'red dendronotid nudibranch'],
        ]
        for names in examples:
            wrong = [sorted(w) for w in verify._find_misspellings(names[:])]
            self.assertEqual(wrong, [])


if __name__ == '__main__':
    unittest.main()
