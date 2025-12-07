import unittest

from util.similarity import similarity


class TestSimilarity(unittest.TestCase):
    """Position-weighted taxonomy similarity tests."""

    def test_identical(self) -> None:
        self.assertEqual(similarity('a b c', 'a b c'), 1.0)

    def test_no_match(self) -> None:
        self.assertEqual(similarity('a b c', 'd e f'), 0.0)

    def test_shorter_less_similar(self) -> None:
        s1 = similarity('a b', 'a b c')
        s2 = similarity('a b c', 'a b c')
        self.assertLess(s1, s2)

    def test_more_matches_more_similar(self) -> None:
        s1 = similarity('a', 'a b c')
        s2 = similarity('a b', 'a b c')
        self.assertLess(s1, s2)

    def test_position_independent_for_same_match_count(self) -> None:
        s1 = similarity('a b c', 'a b d')
        s2 = similarity('d e f', 'd e g')
        self.assertEqual(s1, s2)

    def test_early_divergence_worse(self) -> None:
        """Early divergence (kingdom) is worse than late divergence (species)."""
        s1 = similarity('a b c d', 'x b c d')  # kingdom mismatch: (3+2+1)/10 = 0.6
        s2 = similarity('a b c d', 'a b c x')  # species mismatch: (4+3+2)/10 = 0.9
        self.assertLess(s1, s2)

    def test_large_depth_difference(self) -> None:
        """Large depth difference results in low similarity."""
        score = similarity('a', 'a b c d e f')  # 6/21 ≈ 0.286
        self.assertLess(score, 0.3)
        self.assertGreater(score, 0.0)

    def test_same_depth_no_match(self) -> None:
        """Same depth but no matches = 0.0."""
        self.assertEqual(similarity('a b c', 'x y z'), 0.0)

    def test_empty_strings(self) -> None:
        """Empty strings return 0.0."""
        self.assertEqual(similarity('', 'a b c'), 0.0)
        self.assertEqual(similarity('a b c', ''), 0.0)
        self.assertEqual(similarity('', ''), 0.0)


if __name__ == '__main__':
    unittest.main()
