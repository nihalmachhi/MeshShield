"""Small calibration and review-capacity helpers for binary scores."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PlattCalibrator:
    slope: float
    intercept: float

    def apply(self, score: float) -> float:
        probability = min(max(score, 1e-8), 1 - 1e-8)
        logit = math.log(probability / (1 - probability))
        value = self.slope * logit + self.intercept
        return 1 / (1 + math.exp(-max(-35.0, min(35.0, value))))


def fit_platt(
    scores: list[float], labels: list[int], epochs: int = 500, learning_rate: float = 0.01
) -> PlattCalibrator:
    if len(scores) != len(labels) or not scores or len(set(labels)) < 2:
        raise ValueError("calibration needs matching scores and both label classes")
    if any(label not in (0, 1) for label in labels) or any(not 0 <= score <= 1 for score in scores):
        raise ValueError("calibration labels and scores must be in [0, 1]")
    logits = [
        math.log(min(max(score, 1e-8), 1 - 1e-8) / (1 - min(max(score, 1e-8), 1 - 1e-8)))
        for score in scores
    ]
    slope, intercept = 1.0, 0.0
    for _ in range(epochs):
        slope_gradient = intercept_gradient = 0.0
        for logit, label in zip(logits, labels):
            prediction = 1 / (1 + math.exp(-max(-35.0, min(35.0, slope * logit + intercept))))
            error = prediction - label
            slope_gradient += error * logit
            intercept_gradient += error
        scale = learning_rate / len(labels)
        slope -= scale * slope_gradient
        intercept -= scale * intercept_gradient
    return PlattCalibrator(slope, intercept)


def select_cost_threshold(
    labels: list[int],
    scores: list[float],
    false_positive_cost: float,
    false_negative_cost: float,
    review_capacity: float,
) -> dict[str, float]:
    if len(labels) != len(scores) or not labels:
        raise ValueError("threshold selection needs matching non-empty labels and scores")
    costs = (false_positive_cost, false_negative_cost, review_capacity)
    if (
        any(not math.isfinite(value) for value in costs)
        or false_positive_cost < 0
        or false_negative_cost < 0
        or not 0 <= review_capacity <= 1
    ):
        raise ValueError("costs must be non-negative and capacity must be in [0, 1]")
    if any(label not in (0, 1) for label in labels) or any(not 0 <= score <= 1 for score in scores):
        raise ValueError("threshold labels and scores must be in [0, 1]")
    candidate_values = {0.0, 1.0, *scores}
    if max(scores) < 1:
        candidate_values.add(math.nextafter(max(scores), math.inf))
    candidates = sorted(candidate_values)
    choices = []
    for threshold in candidates:
        selected = [score >= threshold for score in scores]
        review_rate = sum(selected) / len(scores)
        if review_rate <= review_capacity:
            cost = sum(
                false_positive_cost
                for label, flagged in zip(labels, selected)
                if flagged and label == 0
            )
            cost += sum(
                false_negative_cost
                for label, flagged in zip(labels, selected)
                if not flagged and label == 1
            )
            choices.append((cost, threshold, review_rate))
    cost, threshold, review_rate = min(choices, key=lambda item: (item[0], -item[1]))
    return {"threshold": threshold, "expected_cost": cost / len(labels), "review_rate": review_rate}
