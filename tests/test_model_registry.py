"""Every registered model must fit, score, persist and fail clearly."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from meshshield.config import FEATURES, GRAPH_FEATURES
from meshshield.models.isolation_forest import IsolationForestModel
from meshshield.models.logistic import LogisticModel
from meshshield.models.registry import (
    Model,
    available_models,
    create_model,
    load_model,
    save_model,
)


def rows(count: int = 120) -> tuple[list[list[float]], list[int]]:
    features = []
    labels = []
    for index in range(count):
        features.append([float(index % 7), float(index % 3), float(index // 10)])
        labels.append(1 if index % 5 == 0 else 0)
    return features, labels


def test_catalog_reports_live_availability() -> None:
    catalog = available_models()
    assert set(catalog) == {"logistic", "lightgbm", "isolation-forest"}
    assert catalog["logistic"]["available"] is True
    assert catalog["isolation-forest"]["available"] is True
    expected = importlib.util.find_spec("lightgbm") is not None
    assert catalog["lightgbm"]["available"] is expected


def test_unknown_model_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown model"):
        create_model("magic", [[0.0]], [0], ("x",))


def test_logistic_round_trip(tmp_path: Path) -> None:
    features, labels = rows()
    model: Model = create_model("logistic", features, labels, ("a", "b", "c"))
    assert isinstance(model, LogisticModel)
    path = tmp_path / "model.json"
    save_model(model, path)
    loaded = load_model(path)
    assert loaded.score(features[0]) == model.score(features[0])
    assert json.loads(path.read_text(encoding="utf-8"))["kind"] == "logistic"


def test_isolation_forest_is_deterministic_and_bounded() -> None:
    features, _ = rows()
    first = IsolationForestModel.fit(features, ("a", "b", "c"), trees=20)
    second = IsolationForestModel.fit(features, ("a", "b", "c"), trees=20)
    scores = [first.score(row) for row in features]
    assert scores == [second.score(row) for row in features]
    assert all(0.0 <= score <= 1.0 for score in scores)
    assert first.contributions(features[0]) == []


def test_isolation_forest_round_trip(tmp_path: Path) -> None:
    features, _ = rows()
    model = IsolationForestModel.fit(features, ("a", "b", "c"), trees=10)
    path = tmp_path / "forest.json"
    model.save(path)
    loaded = IsolationForestModel.load(path)
    assert isinstance(load_model(path), IsolationForestModel)
    assert loaded.score(features[3]) == model.score(features[3])


def test_feature_sets_stay_in_sync() -> None:
    assert set(FEATURES).issubset(GRAPH_FEATURES)
    assert len(GRAPH_FEATURES) == len(set(GRAPH_FEATURES))


def test_pipeline_trains_and_reloads_an_anomaly_model(isolated_paths: dict[str, Path]) -> None:
    from meshshield.core import pipeline

    pipeline.generate_dataset(count=400, seed=7)
    metrics = pipeline.train_and_evaluate("isolation-forest")
    assert metrics["model_selection"]["selected"] == "isolation-forest"
    saved = json.loads(isolated_paths["model"].read_text(encoding="utf-8"))
    assert saved["kind"] == "isolation_forest"
    loaded = load_model(isolated_paths["model"])
    assert isinstance(loaded, IsolationForestModel)
    assert loaded.feature_names == GRAPH_FEATURES

