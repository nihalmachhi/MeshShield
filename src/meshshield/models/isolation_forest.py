"""A small, dependency-free Isolation Forest with deterministic trees.

This is an unsupervised anomaly detector: it never reads the labels. Scores are
in ``[0, 1]``, higher meaning more isolated, and can be calibrated like any other
score. The implementation is deliberately compact so the model can be saved as
plain JSON and inspected by hand.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

Node = dict[str, Any]
_EULER_GAMMA = 0.5772156649015329


def _average_path_length(size: int) -> float:
    if size <= 1:
        return 0.0
    return 2.0 * (math.log(size - 1) + _EULER_GAMMA) - 2.0 * (size - 1) / size


def _build_tree(
    rows: list[list[float]], depth: int, height: int, rng: random.Random, width: int
) -> Node:
    if depth >= height or len(rows) <= 1:
        return {"s": len(rows)}
    candidate = [
        feature
        for feature in rng.sample(range(width), width)
        if max(row[feature] for row in rows) > min(row[feature] for row in rows)
    ]
    if not candidate:
        return {"s": len(rows)}
    feature = candidate[0]
    low = min(row[feature] for row in rows)
    high = max(row[feature] for row in rows)
    split = low + rng.random() * (high - low)
    left = [row for row in rows if row[feature] < split]
    right = [row for row in rows if row[feature] >= split]
    if not left or not right:
        return {"s": len(rows)}
    return {
        "f": feature,
        "v": split,
        "l": _build_tree(left, depth + 1, height, rng, width),
        "r": _build_tree(right, depth + 1, height, rng, width),
    }


def _path_length(node: Node, values: list[float]) -> float:
    depth = 0
    while "s" not in node:
        depth += 1
        node = node["l"] if values[node["f"]] < node["v"] else node["r"]
    return depth + _average_path_length(int(node["s"]))


class IsolationForestModel:
    """Deterministic Isolation Forest with JSON persistence."""

    kind = "isolation_forest"

    def __init__(self, feature_names: tuple[str, ...], trees: list[Node], sample_size: int):
        if not trees or sample_size < 2:
            raise ValueError("an isolation forest needs trees and a sample of at least two rows")
        self.feature_names = feature_names
        self.trees = trees
        self.sample_size = sample_size

    @classmethod
    def fit(
        cls,
        rows: list[list[float]],
        feature_names: tuple[str, ...],
        *,
        trees: int = 60,
        sample_size: int = 128,
        random_seed: int = 2025,
    ) -> IsolationForestModel:
        if not rows or len(feature_names) == 0:
            raise ValueError("training needs rows and a non-empty feature list")
        width = len(feature_names)
        if any(len(row) != width for row in rows):
            raise ValueError("every training row must match the non-empty feature list")
        if any(not math.isfinite(value) for row in rows for value in row):
            raise ValueError("training features must be finite")
        if trees < 1 or sample_size < 2:
            raise ValueError("trees must be positive and sample_size at least two")
        rng = random.Random(random_seed)
        height = max(1, math.ceil(math.log2(min(sample_size, len(rows)))))
        size = min(sample_size, len(rows))
        forest = [
            _build_tree(
                [rows[rng.randrange(len(rows))] for _ in range(size)],
                0,
                height,
                rng,
                width,
            )
            for _ in range(trees)
        ]
        return cls(feature_names, forest, size)

    def score(self, values: list[float]) -> float:
        if len(values) != len(self.feature_names) or any(
            not math.isfinite(value) for value in values
        ):
            raise ValueError("score row must match the model's finite feature vector")
        denominator = _average_path_length(self.sample_size) or 1.0
        mean_path = sum(_path_length(tree, values) for tree in self.trees) / len(self.trees)
        score = 2.0 ** (-mean_path / denominator)
        return float(min(1.0, max(0.0, score)))

    def contributions(self, values: list[float], limit: int = 4) -> list[dict[str, float | str]]:
        # Isolation Forest paths are not additive, so there is no honest per-row
        # contribution to report. The UI falls back to the score alone.
        if len(values) != len(self.feature_names) or limit < 1:
            raise ValueError("contribution row width and limit must be valid")
        return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "feature_names": list(self.feature_names),
            "trees": self.trees,
            "sample_size": self.sample_size,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> IsolationForestModel:
        return cls(tuple(value["feature_names"]), value["trees"], int(value["sample_size"]))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict()), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> IsolationForestModel:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
