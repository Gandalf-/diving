from typing import Any

import pytest

import diving.util.common as utility


class TestUtility:
    """utility.py"""

    def test_walk_spine(self) -> None:
        """it works"""
        tree = {'a': {'b': {'c': 1}}}
        assert utility.walk_spine(tree, ['a']) == {'b': {'c': 1}}
        assert utility.walk_spine(tree, ['a', 'b']) == {'c': 1}
        assert utility.walk_spine(tree, ['a', 'b', 'c']) == 1

    def test_prefix_tuples(self) -> None:
        """it works"""
        out = utility.prefix_tuples(1, [(2, 3), (3, 4), (4, 5)])
        out = list(out)
        assert out == [(1, 2, 3), (1, 3, 4), (1, 4, 5)]

    @pytest.mark.parametrize(
        'date,expected',
        [
            ('2023-01-01', 'January 1st, 2023'),
            ('2023-01-11', 'January 11th, 2023'),
            ('2023-01-12', 'January 12th, 2023'),
            ('2023-01-13', 'January 13th, 2023'),
            ('2023-10-02', 'October 2nd, 2023'),
            ('2023-10-22', 'October 22nd, 2023'),
            ('2023-12-03', 'December 3rd, 2023'),
            ('2023-12-23', 'December 23rd, 2023'),
            ('2023-04-04', 'April 4th, 2023'),
            ('2023-04-24', 'April 24th, 2023'),
        ],
    )
    def test_pretty_date(self, date: str, expected: str) -> None:
        assert utility.pretty_date(date) == expected

    def test_take(self) -> None:
        """it works"""
        assert utility.take([1, 2, 3, 4, 5], 3) == [1, 2, 3]
        assert utility.take([1, 2, 3], 5) == [1, 2, 3]
        assert utility.take([1, 2, 3, 4, 5], 0) == []
        assert utility.take(range(100000000), 5) == [0, 1, 2, 3, 4]

    def test_flatten(self) -> None:
        """it works"""
        assert [0, 1, 2] == utility.flatten([[0], [1, 2]])
        assert [] == utility.flatten([[]])

    def test_tree_size(self) -> None:
        """Test the tree_size function with various inputs."""
        # Test a tree with no leaves
        tree: dict[str, Any] = {'a': {'b': {}, 'c': {}}, 'd': {}}
        assert utility.tree_size(tree) == 0

        # Test a tree with one leaf
        tree = {'a': {'b': {'c': [1]}}}
        assert utility.tree_size(tree) == 1

        # Test a tree with multiple leaves
        tree = {'a': {'b': [3, 3]}, 'c': [4, 4, 4]}
        assert utility.tree_size(tree) == 5

        # Test a tree with nested leaves
        tree = {'a': {'b': {'c': {'d': [1]}}}}
        assert utility.tree_size(tree) == 1

        # Test a tree with multiple levels
        tree = {'a': {'b': {'c': {'d': [1, 2, 3]}}, 'e': {'f': [4]}}, 'g': [5]}
        assert utility.tree_size(tree) == 5

    def test_extract_leaves(self) -> None:
        """grab the leaves for this tree"""
        tree = {'a': {'b': 3}, 'c': 4}
        leaves = list(utility.extract_leaves(tree))
        wanted = [3, 4]
        assert sorted(leaves) == sorted(wanted)

    def test_extract_branches(self) -> None:
        """grab the branches for this tree"""
        tree = {'a': {'b': 3}, 'c': 4}
        branches = list(utility.extract_branches(tree))
        wanted = ['a', 'b', 'c']
        assert sorted(branches) == sorted(wanted)

    def test_hmap(self) -> None:
        """fold-ish thing"""
        assert utility.hmap(0, lambda x: x + 1, lambda x: x * 5) == 5
        assert utility.hmap(0, lambda x: x + 1, lambda x: x * 5, lambda x: x - 1) == 4
        assert (
            utility.hmap(0, lambda x: x + 1, lambda x: x * 5, lambda x: x - 1, lambda x: x / 2)
            == 2.0
        )

    @pytest.mark.parametrize(
        'date,expected',
        [
            ('2017-01-01', True),
            ('2000-11-21', True),
            ('2000-91-21', False),
            ('2000-21', False),
        ],
    )
    def test_is_date(self, date: str, expected: bool) -> None:
        assert utility.is_date(date) == expected

    @pytest.mark.parametrize(
        'before,expected',
        [
            ('Sund Rock 2017-01-01', 'Sund Rock'),
            ('Sund Rock 4', 'Sund Rock 4'),
            ('2017-01-01', '2017-01-01'),
        ],
    )
    def test_strip_date(self, before: str, expected: str) -> None:
        assert utility.strip_date(before) == expected

    def test_file_content_matches(self) -> None:
        """it works"""
        with open('LICENSE') as fd:
            license = fd.read()

        assert utility.file_content_matches('LICENSE', license) is True
        assert utility.file_content_matches('LICENSE', 'Hello there') is False
        assert utility.file_content_matches('LICENSE', license.replace(' ', '!')) is False
