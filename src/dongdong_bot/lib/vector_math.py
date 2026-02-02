from __future__ import annotations

from math import sqrt
from typing import Iterable, Sequence


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    denom = sqrt(norm_a) * sqrt(norm_b)
    if denom == 0.0:
        return 0.0
    return dot / denom


def top_k_scored(items: Iterable[tuple[str, float]], k: int) -> list[tuple[str, float]]:
    return sorted(items, key=lambda item: item[1], reverse=True)[:k]
