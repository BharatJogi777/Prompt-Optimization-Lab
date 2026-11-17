"""Dependency-free ranking metrics for retrieval evaluation."""

from __future__ import annotations

from math import log2
from typing import Hashable, Iterable, Sequence, TypeVar

T = TypeVar("T", bound=Hashable)


def _validate_k(k: int) -> None:
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("k must be a positive integer")


def _relevant_set(relevant_ids: Iterable[T]) -> set[T]:
    return set(relevant_ids)


def precision_at_k(
    retrieved_ids: Sequence[T],
    relevant_ids: Iterable[T],
    k: int,
) -> float:
    """Fraction of the first k result slots that are relevant.

    K is the denominator even when fewer than K results were returned.
    """
    _validate_k(k)
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0
    return sum(1 for item_id in retrieved_ids[:k] if item_id in relevant) / k


def recall_at_k(
    retrieved_ids: Sequence[T],
    relevant_ids: Iterable[T],
    k: int,
) -> float:
    """Fraction of all known relevant IDs found in the first k results."""
    _validate_k(k)
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0
    found = set(retrieved_ids[:k]).intersection(relevant)
    return len(found) / len(relevant)


def hit_rate_at_k(
    retrieved_ids: Sequence[T],
    relevant_ids: Iterable[T],
    k: int,
) -> float:
    """1.0 if at least one relevant item appears in the first k, else 0.0."""
    _validate_k(k)
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0
    return float(any(item_id in relevant for item_id in retrieved_ids[:k]))


def reciprocal_rank(
    retrieved_ids: Sequence[T],
    relevant_ids: Iterable[T],
) -> float:
    """Reciprocal rank of the first relevant result, or zero."""
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    ranked_results: Sequence[Sequence[T]],
    relevance_judgments: Sequence[Iterable[T]],
) -> float:
    """Macro-averaged reciprocal rank across queries."""
    if len(ranked_results) != len(relevance_judgments):
        raise ValueError("ranked_results and relevance_judgments must have equal length")
    if not ranked_results:
        return 0.0
    scores = [
        reciprocal_rank(results, relevant)
        for results, relevant in zip(ranked_results, relevance_judgments)
    ]
    return sum(scores) / len(scores)


def ndcg_at_k(
    retrieved_ids: Sequence[T],
    relevant_ids: Iterable[T],
    k: int,
) -> float:
    """nDCG@K using binary relevance and logarithmic rank discount."""
    _validate_k(k)
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0

    dcg = sum(
        1.0 / log2(rank + 1)
        for rank, item_id in enumerate(retrieved_ids[:k], start=1)
        if item_id in relevant
    )
    ideal_count = min(len(relevant), k)
    ideal_dcg = sum(
        1.0 / log2(rank + 1)
        for rank in range(1, ideal_count + 1)
    )
    return dcg / ideal_dcg if ideal_dcg else 0.0
