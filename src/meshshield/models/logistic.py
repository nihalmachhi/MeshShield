"""Dependency-free standardized logistic regression for a transparent baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from meshshield.config import FEATURES, GRAPH_FEATURES


def _sigmoid(value: float) -> float:
    value = max(-35.0, min(35.0, value))
    return 1.0 / (1.0 + math.exp(-value))


class LogisticModel:
    def __init__(
        self,
        feature_names: tuple[str, ...],
        means: list[float],
        scales: list[float],
        weights: list[float],
        bias: float,
    ):
        self.feature_names = feature_names
        self.means, self.scales, self.weights, self.bias = means, scales, weights, bias

    @classmethod
    def fit(
        cls,
        rows: list[list[float]],
        labels: list[int],
        feature_names: tuple[str, ...],
        epochs: int = 700,
        learning_rate: float = 0.08,
        regularization: float = 0.015,
        tolerance: float = 1e-7,
        patience: int = 12,
    ) -> LogisticModel:
        if not rows or len(rows) != len(labels) or len(set(labels)) < 2:
            raise ValueError("Training data needs matching rows and both label classes.")
        if any(label not in (0, 1) for label in labels):
            raise ValueError("labels must contain only 0 or 1")
        width = len(feature_names)
        if width == 0 or any(len(row) != width for row in rows):
            raise ValueError("every training row must match the non-empty feature list")
        if any(not math.isfinite(value) for row in rows for value in row):
            raise ValueError("training features must be finite")
        if epochs < 1 or learning_rate <= 0 or regularization < 0 or tolerance < 0 or patience < 1:
            raise ValueError("training settings are outside their valid ranges")
        means = [sum(row[j] for row in rows) / len(rows) for j in range(width)]
        scales = []
        for j in range(width):
            variance = sum((row[j] - means[j]) ** 2 for row in rows) / len(rows)
            scales.append(math.sqrt(variance) or 1.0)
        normalized = [[(row[j] - means[j]) / scales[j] for j in range(width)] for row in rows]
        class_counts = {label: labels.count(label) for label in (0, 1)}
        sample_weights = [len(labels) / (2 * class_counts[label]) for label in labels]
        weight_total = sum(sample_weights)
        weights, bias = [0.0] * width, 0.0
        previous_loss = float("inf")
        stable_epochs = 0
        for _epoch in range(epochs):
            grad = [0.0] * width
            grad_bias = 0.0
            loss = 0.0
            for row, label, sample_weight in zip(normalized, labels, sample_weights):
                error = _sigmoid(bias + sum(w * x for w, x in zip(weights, row))) - label
                probability = min(max(error + label, 1e-15), 1 - 1e-15)
                loss -= sample_weight * (
                    label * math.log(probability) + (1 - label) * math.log(1 - probability)
                )
                grad_bias += sample_weight * error
                for j, value in enumerate(row):
                    grad[j] += sample_weight * error * value
            loss = loss / weight_total + 0.5 * regularization * sum(w * w for w in weights)
            step = learning_rate
            for j in range(width):
                weights[j] -= step * (grad[j] / weight_total + regularization * weights[j])
            bias -= step * grad_bias / weight_total
            if abs(previous_loss - loss) < tolerance:
                stable_epochs += 1
                if stable_epochs >= patience:
                    break
            else:
                stable_epochs = 0
            previous_loss = loss
        return cls(feature_names, means, scales, weights, bias)

    def score(self, values: list[float]) -> float:
        if len(values) != len(self.feature_names) or any(
            not math.isfinite(value) for value in values
        ):
            raise ValueError("score row must match the model's finite feature vector")
        normalized = [(x - m) / s for x, m, s in zip(values, self.means, self.scales)]
        return _sigmoid(self.bias + sum(w * x for w, x in zip(self.weights, normalized)))

    def contributions(self, values: list[float], limit: int = 4) -> list[dict[str, float | str]]:
        if len(values) != len(self.feature_names) or limit < 1:
            raise ValueError("contribution row width and limit must be valid")
        items: list[dict[str, float | str]] = []
        for name, value, mean, scale, weight in zip(
            self.feature_names, values, self.means, self.scales, self.weights
        ):
            items.append({"feature": name, "contribution": weight * (value - mean) / scale})
        return sorted(
            items,
            key=lambda item: (
                abs(item["contribution"]) if isinstance(item["contribution"], float) else 0.0
            ),
            reverse=True,
        )[:limit]

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_names": list(self.feature_names),
            "means": self.means,
            "scales": self.scales,
            "weights": self.weights,
            "bias": self.bias,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> LogisticModel:
        return cls(
            tuple(value["feature_names"]),
            value["means"],
            value["scales"],
            value["weights"],
            value["bias"],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> LogisticModel:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def feature_names(graph: bool) -> tuple[str, ...]:
    return GRAPH_FEATURES if graph else FEATURES
