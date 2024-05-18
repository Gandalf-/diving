import unittest
from typing import List

import util.common as utility


class TestUtility(unittest.TestCase):
    """utility.py"""

    def test_walk_spine(self) -> None:
        """it works"""
        tree = {'a': {'b': {'c': 1}}}
        self.assertEqual(utility.walk_spine(tree, ['a']), {'b': {'c': 1}})
        self.assertEqual(utility.walk_spine(tree, ['a', 'b']), {'c': 1})
        self.assertEqual(utility.walk_spine(tree, ['a', 'b', 'c']), 1)

    def test_prefix_tuples(self) -> None:
        """it works"""
        out = utility.prefix_tuples(1, [(2, 3), (3, 4), (4, 5)])
        out = list(out)
        self.assertEqual(out, [(1, 2, 3), (1, 3, 4), (1, 4, 5)])

    def test_pretty_date(self) -> None:
        pairs = [
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
        ]
        for before, after in pairs:
            self.assertEqual(utility.pretty_date(before), after)

    def test_take(self) -> None:
        """it works"""
        xs = [1, 2, 3, 4, 5]
        n = 3
        expected = [1, 2, 3]
        self.assertEqual(utility.take(xs, n), expected)

        xs = [1, 2, 3]
        n = 5
        expected = [1, 2, 3]
        self.assertEqual(utility.take(xs, n), expected)

        xs = [1, 2, 3, 4, 5]
        n = 0
        expected: List[int] = []
        self.assertEqual(utility.take(xs, n), expected)

        xs = range(100000000)
        n = 5
        expected = [0, 1, 2, 3, 4]
        self.assertEqual(utility.take(xs, n), expected)

    def test_flatten(self) -> None:
        """it works"""
        self.assertEqual([0, 1, 2], utility.flatten([[0], [1, 2]]))
        self.assertEqual([], utility.flatten([[]]))

    def test_tree_size(self) -> None:
        """Test the tree_size function with various inputs."""
        # Test a tree with no leaves
        tree = {'a': {'b': {}, 'c': {}}, 'd': {}}
        self.assertEqual(utility.tree_size(tree), 0)

        # Test a tree with one leaf
        tree = {'a': {'b': {'c': [1]}}}
        self.assertEqual(utility.tree_size(tree), 1)

        # Test a tree with multiple leaves
        tree = {'a': {'b': [3, 3]}, 'c': [4, 4, 4]}
        self.assertEqual(utility.tree_size(tree), 5)

        # Test a tree with nested leaves
        tree = {'a': {'b': {'c': {'d': [1]}}}}
        self.assertEqual(utility.tree_size(tree), 1)

        # Test a tree with multiple levels
        tree = {'a': {'b': {'c': {'d': [1, 2, 3]}}, 'e': {'f': [4]}}, 'g': [5]}
        self.assertEqual(utility.tree_size(tree), 5)

    def test_extract_leaves(self) -> None:
        """grab the leaves for this tree"""
        tree = {'a': {'b': 3}, 'c': 4}
        leaves = list(utility.extract_leaves(tree))
        wanted = [3, 4]
        self.assertEqual(sorted(leaves), sorted(wanted))

    def test_extract_branches(self) -> None:
        """grab the branches for this tree"""
        tree = {'a': {'b': 3}, 'c': 4}
        branches = list(utility.extract_branches(tree))
        wanted = ['a', 'b', 'c']
        self.assertEqual(sorted(branches), sorted(wanted))

    def test_hmap(self) -> None:
        """fold-ish thing"""
        out = utility.hmap(0, lambda x: x + 1, lambda x: x * 5)
        self.assertEqual(out, 5)

        out = utility.hmap(0, lambda x: x + 1, lambda x: x * 5, lambda x: x - 1)
        self.assertEqual(out, 4)

        out = utility.hmap(0, lambda x: x + 1, lambda x: x * 5, lambda x: x - 1, lambda x: x / 2)
        self.assertEqual(out, 2.0)

    def test_is_date(self) -> None:
        """it works"""
        for positive in ('2017-01-01', '2000-11-21'):
            self.assertTrue(utility.is_date(positive))

        for negative in ('2000-91-21', '2000-21', '2000-21'):
            self.assertFalse(utility.is_date(negative))

    def test_strip_date(self) -> None:
        """it works"""
        examples = [
            ('Sund Rock 2017-01-01', 'Sund Rock'),
            ('Sund Rock 4', 'Sund Rock 4'),
            ('2017-01-01', '2017-01-01'),
        ]
        for before, after in examples:
            self.assertEqual(utility.strip_date(before), after)

    def test_file_content_matches(self) -> None:
        """it works"""
        with open('LICENSE') as fd:
            license = fd.read()

        self.assertTrue(utility.file_content_matches('LICENSE', license))

        self.assertFalse(utility.file_content_matches('LICENSE', 'Hello there'))
        self.assertFalse(utility.file_content_matches('LICENSE', license.replace(' ', '!')))


if __name__ == '__main__':
    unittest.main()
