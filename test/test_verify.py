from typing import Any

import pytest

from diving.util import collection, verify


class TestVerify:
    """verify.py"""

    def _build_swapped_tree(self) -> collection.ImageTree:
        """swapped words"""
        tree: Any = collection.build_image_tree()
        nudi = tree['nudibranch']['sea lemon']['freckled pale']['data'].pop()
        nudi.name = 'Pale Freckled Sea Lemon'

        tree['nudibranch']['sea lemon']['pale freckled'] = {'data': [nudi]}

        assert 'pale freckled' in tree['nudibranch']['sea lemon'].keys()
        assert 'freckled pale' in tree['nudibranch']['sea lemon'].keys()

        return tree

    def test_detect_wrong_name_order(self) -> None:
        """pale freckled sea lemon vs freckled pale sea lemon"""
        tree = self._build_swapped_tree()
        wrong = list(verify._find_wrong_name_order(tree))
        assert wrong == [('freckled pale', 'pale freckled')]

    @pytest.mark.parametrize(
        'names,expected',
        [
            (
                ['curlyhead spaghetti worm', 'curlyheaded spaghetti worm'],
                [['curlyhead spaghetti worm', 'curlyheaded spaghetti worm']],
            ),
            (
                ['encrusting bryozoan', 'encrusting byrozoan'],
                [['encrusting bryozoan', 'encrusting byrozoan']],
            ),
            (
                ['nanaimo nudibranch', 'naniamo nudibranch'],
                [['nanaimo nudibranch', 'naniamo nudibranch']],
            ),
        ],
    )
    def test_detect_misspelling(self, names: list[str], expected: list[list[str]]) -> None:
        """curlyhead spaghetti worm vs curlyheaded spaghetti worm"""
        wrong = [sorted(w) for w in verify._possible_misspellings(set(names))]
        assert wrong == expected

    @pytest.mark.parametrize(
        'names',
        [
            ['submerged log', 'submerged wood'],
            ['a unknown', 'b unknown'],
        ],
    )
    def test_detect_misspelling_ignore_explicit(self, names: list[str]) -> None:
        """don't consider ignored names"""
        wrong = [sorted(w) for w in verify._possible_misspellings(set(names))]
        assert wrong == []

    @pytest.mark.parametrize(
        'names',
        [
            ['dalls dendronotid nudibranch', 'red dendronotid nudibranch'],
        ],
    )
    def test_detect_misspelling_ignore_scientific(self, names: list[str]) -> None:
        """a name isn't misspelled if it has a scientific name"""
        wrong = [sorted(w) for w in verify._find_misspellings(set(names))]
        assert wrong == []
