"""End-to-end pipeline behaviour: generation, training, scoring and the CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from conftest import make_transaction

from meshshield.core import pipeline
from meshshield.features.build import build_features, vector
from meshshield.models.logistic import LogisticModel, feature_names


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """Train once on a small isolated dataset and share the result."""
    return {}


def test_train_and_evaluate_writes_every_artifact(isolated_paths: dict[str, Path]) -> None:
    pipeline.generate_dataset(400, seed=2025)
    metrics = pipeline.train_and_evaluate()

    for name in ("model", "baseline_model", "metrics", "calibration", "card"):
        assert isolated_paths[name].exists(), f"{name} was not written"

    assert set(metrics) >= {
        "dataset",
        "graph_model",
        "graph_model_calibrated",
        "non_graph_model",
        "rule_only_baseline",
        "full_decision_pipeline",
        "threshold_policy",
        "feature_drift_psi",
    }
    assert metrics["dataset"]["transactions"] == 400
    assert sum(metrics["dataset"][key] for key in ("train", "calibration", "test")) == 400
    assert 0.0 <= metrics["graph_model_calibrated"]["recall"] <= 1.0


def test_metrics_are_reproducible_on_the_same_seed(isolated_paths: dict[str, Path]) -> None:
    pipeline.generate_dataset(300, seed=5)
    first = pipeline.train_and_evaluate()
    second = pipeline.train_and_evaluate()
    assert first == second


def test_saved_model_round_trips_through_load_or_prepare(isolated_paths: dict[str, Path]) -> None:
    pipeline.generate_dataset(300, seed=6)
    pipeline.train_and_evaluate()
    transactions, metrics, model, calibrator, threshold = pipeline.load_or_prepare()

    assert len(transactions) == 300
    assert metrics["dataset"]["transactions"] == 300
    assert isinstance(model, LogisticModel)
    assert 0.0 <= threshold <= 1.0
    assert 0.0 <= calibrator.apply(0.5) <= 1.0


def test_scoring_explains_itself() -> None:
    known = [make_transaction(i, amount=20.0, account_id=f"acct_{i:03d}") for i in range(30)]
    known += [make_transaction(100 + i, amount=900.0, label=1) for i in range(5)]
    rows = build_features(known)
    model = LogisticModel.fit(
        [vector(rows[tx.transaction_id]) for tx in known],
        [int(tx.label or 0) for tx in known],
        feature_names(graph=True),
        epochs=80,
    )
    target = known[-1]
    result = pipeline.score_transaction(target, known[:-1], model, feature_rows=rows)

    assert set(result) >= {"risk_score", "decision", "integrity_findings", "top_contributions"}
    assert 0.0 <= result["risk_score"] <= 1.0
    assert result["decision"] in {"review", "low_risk"}
    assert result["top_contributions"]


def test_a_bad_signature_forces_review() -> None:
    known = [make_transaction(i) for i in range(10)]
    bad = make_transaction(99, signature_valid=False)
    rows = build_features([*known, bad])
    model = LogisticModel.fit(
        [vector(rows[tx.transaction_id]) for tx in known],
        [0, 1] * 5,
        feature_names(graph=True),
        epochs=20,
    )
    result = pipeline.score_transaction(bad, known, model, feature_rows=rows)
    assert result["decision"] == "review"
    assert "invalid_simulated_signature" in result["integrity_findings"]


def test_cli_generate_and_evaluate(
    isolated_paths: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from meshshield import cli

    monkeypatch.setattr(sys, "argv", ["meshshield", "generate", "--count", "200", "--seed", "4"])
    cli.main()
    generated = json.loads(capsys.readouterr().out)
    assert generated["seed"] == 4

    monkeypatch.setattr(sys, "argv", ["meshshield", "train"])
    cli.main()
    metrics = json.loads(capsys.readouterr().out)
    assert metrics["dataset"]["transactions"] == 200

    monkeypatch.setattr(sys, "argv", ["meshshield", "evaluate"])
    cli.main()
    assert json.loads(capsys.readouterr().out)["dataset"]["transactions"] == 200
