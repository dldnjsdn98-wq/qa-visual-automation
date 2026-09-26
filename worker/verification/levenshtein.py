from __future__ import annotations

from worker.ocr.errors import AdapterError


def _python_distance(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, 1):
        current = [left_index]
        for right_index, right_char in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def levenshtein_distance(left: str, right: str) -> int:
    try:
        from rapidfuzz.distance import Levenshtein
    except ImportError:
        return _python_distance(left, right)
    distance = Levenshtein.distance(left, right, processor=None)
    if isinstance(distance, bool) or not isinstance(distance, int):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    return distance


def score_ratio(left: str, right: str) -> tuple[int, int]:
    denominator = max(len(left), len(right))
    if denominator == 0:
        return (0, 1)
    distance = levenshtein_distance(left, right)
    return (100 * (denominator - distance), denominator)
