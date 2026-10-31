"""Optional LightGBM wrapper, used only when the ``boost`` extra is installed.

The wrapper keeps the same tiny interface as the other models so the pipeline
can swap it in, and it stores the booster as text instead of a pickle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LightGBMModel:
    kind = "lightgbm"

    def __init__(
        self,
        feature_names: tuple[str, ...],
        booster_text: str,
        importances: dict[str, float],
    ):
        self.feature_names = feature_names
        self.booster_text = booster_text
        self.importances = importances

    @classmethod
    def fit(
        cls,
        rows: list[list[float]],
        labels: list[int],
        feature_names: tuple[str, ...],
        random_seed: int = 2025,
    ) -> LightGBMModel:
        if not rows or len(rows) != len(labels) or len(set(labels)) < 2:
            raise ValueError("LightGBM training needs matching rows and both label classes")
        try:
            import lightgbm as lgb
        except ImportError as exc:
            raise RuntimeError(
                "Install MeshShield with the 'boost' extra to use LightGBM"
            ) from exc
        positives = sum(labels)
        negatives = len(labels) - positives
        classifier = lgb.LGBMClassifier(
            objective="binary",
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=20,
            scale_pos_weight=negatives / positives if positives else 1.0,
            random_state=random_seed,
            n_jobs=1,
            verbose=-1,
        )
        classifier.fit(rows, labels)
        booster = classifier.booster_
        gains = booster.feature_importance(importance_type="gain")
        importances = {
            name: float(gain) for name, gain in zip(feature_names, gains, strict=True)
        }
        return cls(feature_names, booster.model_to_string(), importances)

    def _booster(self) -> Any:
        import lightgbm as lgb

        return lgb.Booster(model_str=self.booster_text)

    def score(self, values: list[float]) -> float:
        if len(values) != len(self.feature_names):
            raise ValueError("score row must match the model's feature vector")
        probability = float(self._booster().predict([values])[0])
        return min(1.0, max(0.0, probability))

    def contributions(self, values: list[float], limit: int = 4) -> list[dict[str, float | str]]:
        if len(values) != len(self.feature_names) or limit < 1:
            raise ValueError("contribution row width and limit must be valid")
        # Global gain importance is not a per-row explanation, so report nothing
        # rather than pretend it is one.
        return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "feature_names": list(self.feature_names),
            "booster": self.booster_text,
            "importances": self.importances,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> LightGBMModel:
        return cls(tuple(value["feature_names"]), value["booster"], value.get("importances", {}))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict()), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> LightGBMModel:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
