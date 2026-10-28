"""Dependency-free standardized logistic regression for a transparent baseline."""

import json
import math
from pathlib import Path

from meshshield.config import FEATURES, GRAPH_FEATURES


def _sigmoid(value: float) -> float:
    value = max(-35.0, min(35.0, value))
    return 1.0 / (1.0 + math.exp(-value))


class LogisticModel:
    def __init__(self, feature_names: tuple[str, ...], means: list[float], scales: list[float],
                 weights: list[float], bias: float):
        self.feature_names = feature_names
        self.means, self.scales, self.weights, self.bias = means, scales, weights, bias

    @classmethod
    def fit(cls, rows: list[list[float]], labels: list[int], feature_names: tuple[str, ...],
            epochs: int = 700, learning_rate: float = 0.08, regularization: float = 0.015,
            tolerance: float = 1e-7, patience: int = 12):
        if not rows or len(rows) != len(labels) or len(set(labels)) < 2:
            raise ValueError("Training data needs matching rows and both label classes.")
        if any(label not in (0, 1) for label in labels):
            raise ValueError("labels must contain only 0 or 1")
        width = len(feature_names)
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
        for epoch in range(epochs):
            grad = [0.0] * width
            grad_bias = 0.0
            loss = 0.0
            for row, label, sample_weight in zip(normalized, labels, sample_weights):
                error = _sigmoid(bias + sum(w * x for w, x in zip(weights, row))) - label
                probability = min(max(error + label, 1e-15), 1 - 1e-15)
                loss -= sample_weight * (label * math.log(probability) +
                                         (1 - label) * math.log(1 - probability))
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
        normalized = [(x - m) / s for x, m, s in zip(values, self.means, self.scales)]
        return _sigmoid(self.bias + sum(w * x for w, x in zip(self.weights, normalized)))

    def contributions(self, values: list[float], limit: int = 4) -> list[dict[str, float | str]]:
        items = [{"feature": name, "contribution": weight * (value - mean) / scale}
                 for name, value, mean, scale, weight in zip(
                     self.feature_names, values, self.means, self.scales, self.weights)]
        return sorted(items, key=lambda item: abs(float(item["contribution"])), reverse=True)[:limit]

    def to_dict(self) -> dict:
        return {"feature_names": list(self.feature_names), "means": self.means,
                "scales": self.scales, "weights": self.weights, "bias": self.bias}

    @classmethod
    def from_dict(cls, value: dict):
        return cls(tuple(value["feature_names"]), value["means"], value["scales"],
                   value["weights"], value["bias"])

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path):
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def feature_names(graph: bool) -> tuple[str, ...]:
    return GRAPH_FEATURES if graph else FEATURES
