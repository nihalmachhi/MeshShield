"""Metrics for an imbalanced binary classification problem."""

import math
import random
from collections.abc import Callable


def _validate(labels: list[int], scores: list[float]) -> None:
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have the same length")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must contain only 0 or 1")
    if any(not 0 <= score <= 1 for score in scores):
        raise ValueError("scores must be between 0 and 1")


def roc_auc(labels: list[int], scores: list[float]) -> float:
    """Rank-based ROC AUC with average ranks for tied scores."""
    _validate(labels, scores)
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    if not positives or not negatives:
        return 0.5
    ordered = sorted(zip(scores, labels), key=lambda item: item[0])
    ranks = [0.0] * len(ordered)
    index = 0
    while index < len(ordered):
        end = index
        while end + 1 < len(ordered) and ordered[end + 1][0] == ordered[index][0]:
            end += 1
        average_rank = (index + end) / 2 + 1
        for position in range(index, end + 1):
            ranks[position] = average_rank
        index = end + 1
    positive_rank_sum = sum(rank for rank, (_, label) in zip(ranks, ordered) if label == 1)
    count_positive, count_negative = len(positives), len(negatives)
    return (positive_rank_sum - count_positive * (count_positive + 1) / 2) / (
        count_positive * count_negative
    )


def average_precision(labels: list[int], scores: list[float]) -> float:
    """Area under the precision-recall curve, computed by its definition."""
    _validate(labels, scores)
    positives = sum(labels)
    if not positives:
        return 0.0
    seen_positive = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(sorted(zip(scores, labels), reverse=True), 1):
        if label:
            seen_positive += 1
            precision_sum += seen_positive / rank
    return precision_sum / positives


def precision_at_fraction(
    labels: list[int], scores: list[float], fraction: float = 0.1
) -> dict[str, float]:
    """Metrics when only the top ``fraction`` of the queue can be reviewed."""
    _validate(labels, scores)
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    if not labels:
        return {"fraction": fraction, "threshold": 1.0, "precision": 0.0, "recall": 0.0}
    selected = max(1, math.ceil(len(labels) * fraction))
    ranked = sorted(zip(scores, labels), reverse=True)[:selected]
    true_positives = sum(label for _, label in ranked)
    total_positives = sum(labels)
    return {
        "fraction": fraction,
        "threshold": ranked[-1][0],
        "precision": true_positives / selected,
        "recall": true_positives / total_positives if total_positives else 0.0,
    }


def reliability_bins(
    labels: list[int], scores: list[float], bins: int = 10
) -> list[dict[str, float]]:
    """Equal-width reliability curve: mean score against observed rate."""
    _validate(labels, scores)
    if bins < 1:
        raise ValueError("bins must be positive")
    grouped: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for score, label in zip(scores, labels):
        index = min(bins - 1, int(score * bins))
        grouped[index].append((score, label))
    curve = []
    for index, group in enumerate(grouped):
        if not group:
            continue
        mean_score = sum(score for score, _ in group) / len(group)
        observed = sum(label for _, label in group) / len(group)
        curve.append(
            {
                "lower": index / bins,
                "upper": (index + 1) / bins,
                "count": float(len(group)),
                "mean_score": mean_score,
                "observed_rate": observed,
                "gap": abs(mean_score - observed),
            }
        )
    return curve


def expected_calibration_error(labels: list[int], scores: list[float], bins: int = 10) -> float:
    """Sample-weighted mean gap between predicted and observed rates."""
    curve = reliability_bins(labels, scores, bins)
    total = sum(bin_["count"] for bin_ in curve)
    if not total:
        return 0.0
    return sum(bin_["gap"] * bin_["count"] for bin_ in curve) / total


def bootstrap_ci(
    labels: list[int],
    scores: list[float],
    metric: Callable[[list[int], list[float]], float] = roc_auc,
    *,
    resamples: int = 500,
    seed: int = 2025,
    confidence: float = 0.95,
) -> dict[str, float]:
    """Deterministic percentile bootstrap for a metric on one test set."""
    _validate(labels, scores)
    if resamples < 1 or not 0 < confidence < 1:
        raise ValueError("resamples must be positive and confidence in (0, 1)")
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(resamples):
        indices = [rng.randrange(len(labels)) for _ in range(len(labels))]
        sample_labels = [labels[index] for index in indices]
        if len(set(sample_labels)) < 2:
            continue
        values.append(metric(sample_labels, [scores[index] for index in indices]))
    if not values:
        return {"lower": math.nan, "upper": math.nan, "resamples": 0.0}
    values.sort()
    tail = (1 - confidence) / 2
    lower = values[int(tail * (len(values) - 1))]
    upper = values[int((1 - tail) * (len(values) - 1))]
    return {"lower": lower, "upper": upper, "resamples": float(len(values))}


def paired_bootstrap_delta(
    labels: list[int],
    scores_a: list[float],
    scores_b: list[float],
    metric: Callable[[list[int], list[float]], float] = roc_auc,
    *,
    resamples: int = 500,
    seed: int = 2025,
    confidence: float = 0.95,
) -> dict[str, float]:
    """Percentile interval for ``metric(a) - metric(b)`` on the same resamples."""
    _validate(labels, scores_a)
    _validate(labels, scores_b)
    if resamples < 1 or not 0 < confidence < 1:
        raise ValueError("resamples must be positive and confidence in (0, 1)")
    rng = random.Random(seed)
    deltas: list[float] = []
    for _ in range(resamples):
        indices = [rng.randrange(len(labels)) for _ in range(len(labels))]
        sample_labels = [labels[index] for index in indices]
        if len(set(sample_labels)) < 2:
            continue
        deltas.append(
            metric(sample_labels, [scores_a[index] for index in indices])
            - metric(sample_labels, [scores_b[index] for index in indices])
        )
    if not deltas:
        return {"lower": math.nan, "upper": math.nan, "resamples": 0.0}
    deltas.sort()
    tail = (1 - confidence) / 2
    lower = deltas[int(tail * (len(deltas) - 1))]
    upper = deltas[int((1 - tail) * (len(deltas) - 1))]
    return {"lower": lower, "upper": upper, "resamples": float(len(deltas))}


def evaluate(labels: list[int], scores: list[float], threshold: float = 0.5) -> dict[str, object]:
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have the same length")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must contain only 0 or 1")
    if not 0 <= threshold <= 1 or any(not 0 <= score <= 1 for score in scores):
        raise ValueError("threshold and scores must be between 0 and 1")
    tp = sum(y == 1 and p >= threshold for y, p in zip(labels, scores))
    fp = sum(y == 0 and p >= threshold for y, p in zip(labels, scores))
    fn = sum(y == 1 and p < threshold for y, p in zip(labels, scores))
    tn = sum(y == 0 and p < threshold for y, p in zip(labels, scores))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    positives = sum(labels)
    pr_auc = average_precision(labels, scores)
    brier = sum((p - y) ** 2 for y, p in zip(labels, scores)) / len(labels) if labels else 0.0
    top_ten = precision_at_fraction(labels, scores, 0.1)
    return {
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "pr_auc_average_precision": pr_auc,
        "roc_auc": roc_auc(labels, scores),
        "precision_at_10pct": top_ten["precision"],
        "recall_at_10pct": top_ten["recall"],
        "brier_score": brier,
        "expected_calibration_error": expected_calibration_error(labels, scores),
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
        },
        "review_rate": sum(p >= threshold for p in scores) / len(scores) if scores else 0.0,
        "sample_count": len(labels),
        "positive_count": positives,
    }


def split_index(count: int, train_fraction: float = 0.8) -> int:
    return max(1, min(count - 1, int(count * train_fraction)))
