"""Model selection, construction and persistence.

The registry is intentionally small: three implementations, one interface. The
default ``logistic`` model has no dependencies; ``lightgbm`` needs the optional
``boost`` extra; ``isolation-forest`` is the stdlib anomaly detector. Selecting a
model never changes the split, the features or the calibration policy.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Protocol

from meshshield.models.boosting import LightGBMModel
from meshshield.models.isolation_forest import IsolationForestModel
from meshshield.models.logistic import LogisticModel


class Model(Protocol):
    """The shared interface the pipeline and API rely on."""

    feature_names: tuple[str, ...]

    def score(self, values: list[float]) -> float: ...

    def contributions(
        self, values: list[float], limit: int = 4
    ) -> list[dict[str, float | str]]: ...

    def save(self, path: Path) -> None: ...


MODEL_CATALOG: dict[str, dict[str, str | None]] = {
    "logistic": {
        "description": "Standardized logistic regression (stdlib, per-row contributions).",
        "extra": None,
    },
    "lightgbm": {
        "description": "Gradient-boosted trees; global gain importance, no per-row attribution.",
        "extra": "boost",
    },
    "isolation-forest": {
        "description": "Unsupervised stdlib anomaly detector; no attribution.",
        "extra": None,
    },
}


def available_models() -> dict[str, dict[str, object]]:
    """Catalog with a live availability flag for optional backends."""
    catalog: dict[str, dict[str, object]] = {}
    for name, details in MODEL_CATALOG.items():
        extra = details["extra"]
        if extra == "boost":
            installed = importlib.util.find_spec("lightgbm") is not None
        else:
            installed = True
        catalog[name] = {**details, "available": installed}
    return catalog


def create_model(
    name: str, rows: list[list[float]], labels: list[int], feature_names: tuple[str, ...]
) -> Any:
    """Fit one model by name, raising a clear error for an unknown or missing backend."""
    if name not in MODEL_CATALOG:
        raise ValueError(f"unknown model {name!r}; choose one of {tuple(MODEL_CATALOG)}")
    if name == "logistic":
        return LogisticModel.fit(rows, labels, feature_names)
    if name == "lightgbm":
        return LightGBMModel.fit(rows, labels, feature_names)
    if name == "isolation-forest":
        # Labels are intentionally ignored: this model learns the shape of normal
        # traffic, so it is not trained on the generator's scenario labels.
        return IsolationForestModel.fit(rows, feature_names)
    raise ValueError(f"unhandled model {name!r}")


def save_model(model: Any, path: Path) -> None:
    model.save(path)


def load_model(path: Path) -> Any:
    """Load any registered model, assuming logistic for older files without ``kind``."""
    value = json.loads(path.read_text(encoding="utf-8"))
    kind = value.get("kind", "logistic")
    if kind == "lightgbm":
        return LightGBMModel.from_dict(value)
    if kind == "isolation_forest":
        return IsolationForestModel.from_dict(value)
    return LogisticModel.from_dict(value)
