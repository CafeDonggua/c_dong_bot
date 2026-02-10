from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class MemoryQualityMetric:
    metric_name: str
    value: float
    threshold: float
    evaluated_at: datetime

    @property
    def passed(self) -> bool:
        if self.metric_name == "duplicate_rate":
            return self.value <= self.threshold
        return self.value >= self.threshold


@dataclass(frozen=True)
class MemoryQualityReport:
    metrics: List[MemoryQualityMetric]

    @property
    def passed(self) -> bool:
        return all(metric.passed for metric in self.metrics)


def evaluate_memory_quality(
    query: str,
    results: Sequence[str],
    *,
    accuracy_threshold: float,
    relevance_threshold: float,
    duplicate_rate_max: float,
) -> MemoryQualityReport:
    evaluated_at = datetime.now()
    accuracy = _accuracy_score(query, results)
    relevance = _relevance_score(query, results)
    duplicate_rate = _duplicate_rate(results)
    metrics = [
        MemoryQualityMetric(
            metric_name="accuracy",
            value=accuracy,
            threshold=accuracy_threshold,
            evaluated_at=evaluated_at,
        ),
        MemoryQualityMetric(
            metric_name="relevance",
            value=relevance,
            threshold=relevance_threshold,
            evaluated_at=evaluated_at,
        ),
        MemoryQualityMetric(
            metric_name="duplicate_rate",
            value=duplicate_rate,
            threshold=duplicate_rate_max,
            evaluated_at=evaluated_at,
        ),
    ]
    return MemoryQualityReport(metrics=metrics)


def _accuracy_score(query: str, results: Sequence[str]) -> float:
    if not results:
        return 0.0
    tokens = _tokenize(query)
    if not tokens:
        return 0.0
    hits = 0
    for item in results:
        if _match_any(tokens, item):
            hits += 1
    return hits / len(results)


def _relevance_score(query: str, results: Sequence[str]) -> float:
    if not results:
        return 0.0
    tokens = _tokenize(query)
    if not tokens:
        return 0.0
    scores: List[float] = []
    for item in results:
        scores.append(_overlap_ratio(tokens, item))
    return sum(scores) / len(scores)


def _duplicate_rate(results: Sequence[str]) -> float:
    if not results:
        return 0.0
    unique = len(set(item.strip() for item in results if item.strip()))
    if unique == 0:
        return 0.0
    return 1.0 - (unique / len(results))


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9]{2,}|[\u4e00-\u9fff]{2,}", text)
    cleaned = [token.strip() for token in tokens if token.strip()]
    return cleaned


def _match_any(tokens: Iterable[str], text: str) -> bool:
    return any(token in text for token in tokens)


def _overlap_ratio(tokens: Iterable[str], text: str) -> float:
    token_list = list(tokens)
    if not token_list:
        return 0.0
    hits = sum(1 for token in token_list if token in text)
    return hits / len(token_list)
