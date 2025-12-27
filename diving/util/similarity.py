"""Position-weighted taxonomy similarity scoring."""


def similarity(a: str, b: str) -> float:
    """Position-weighted taxonomy similarity.

    Earlier positions (Kingdom, Phylum) are weighted more heavily than later
    positions (Genus, Species). Uses max length as denominator to penalize
    depth differences.

    Returns 0.0 (no match) to 1.0 (identical).
    """
    at = a.split(' ') if a else []
    bt = b.split(' ') if b else []
    max_len = max(len(at), len(bt))
    if max_len == 0:
        return 0.0

    total_weight = max_len * (max_len + 1) // 2
    match_weight = sum(max_len - i for i, (x, y) in enumerate(zip(at, bt)) if x == y)
    return match_weight / total_weight
