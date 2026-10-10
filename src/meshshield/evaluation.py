"""Metrics for an imbalanced binary classification problem."""

def evaluate(labels: list[int], scores: list[float], threshold: float = 0.5) -> dict:
    tp = sum(y == 1 and p >= threshold for y, p in zip(labels, scores))
    fp = sum(y == 0 and p >= threshold for y, p in zip(labels, scores))
    fn = sum(y == 1 and p < threshold for y, p in zip(labels, scores))
    tn = sum(y == 0 and p < threshold for y, p in zip(labels, scores))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    positives = sum(labels)
    ranked = sorted(zip(scores, labels), reverse=True)
    seen_positive = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(ranked, 1):
        if label:
            seen_positive += 1
            precision_sum += seen_positive / rank
    pr_auc = precision_sum / positives if positives else 0.0
    brier = sum((p - y) ** 2 for y, p in zip(labels, scores)) / len(labels) if labels else 0.0
    return {"threshold": threshold, "precision": precision, "recall": recall, "f1": f1,
            "pr_auc_average_precision": pr_auc, "brier_score": brier,
            "confusion_matrix": {"true_positive": tp, "false_positive": fp,
                                 "false_negative": fn, "true_negative": tn},
            "review_rate": sum(p >= threshold for p in scores) / len(scores) if scores else 0.0,
            "sample_count": len(labels), "positive_count": positives}


def split_index(count: int, train_fraction: float = 0.8) -> int:
    return max(1, min(count - 1, int(count * train_fraction)))
