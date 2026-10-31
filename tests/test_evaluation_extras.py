"""Ranking, calibration and uncertainty metrics must be honest and reproducible."""

from __future__ import annotations

import math
from pathlib import Path

from meshshield.eval.metrics import (
    average_precision,
    bootstrap_ci,
    evaluate,
    expected_calibration_error,
    paired_bootstrap_delta,
    precision_at_fraction,
    reliability_bins,
    roc_auc,
)

LABELS = [1, 1, 0, 0, 1, 0, 0, 0]
SCORES = [0.9, 0.8, 0.7, 0.6, 0.55, 0.4, 0.3, 0.2]


def test_roc_auc_handles_perfect_reversed_and_tied_scores() -> None:
    assert roc_auc([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == 1.0
    assert roc_auc([1, 1, 0, 0], [0.1, 0.2, 0.8, 0.9]) == 0.0
    assert roc_auc([1, 0, 1, 0], [0.5, 0.5, 0.5, 0.5]) == 0.5
    assert roc_auc([0, 0], [0.2, 0.4]) == 0.5


def test_average_precision_matches_hand_calculation() -> None:
    # Ranked labels: 1, 1, 0, 0, 1, 0, 0, 0 -> (1/1 + 2/2 + 3/5) / 3
    assert math.isclose(average_precision(LABELS, SCORES), (1 + 1 + 3 / 5) / 3)


def test_precision_at_fraction_reviews_only_the_top_slice() -> None:
    result = precision_at_fraction(LABELS, SCORES, 0.25)
    assert result["precision"] == 1.0
    assert math.isclose(result["recall"], 2 / 3)
    assert result["threshold"] == 0.8


def test_calibration_error_is_zero_for_a_perfect_curve() -> None:
    labels = [0] * 50 + [1] * 50
    scores = [0.05] * 50 + [0.95] * 50
    assert expected_calibration_error(labels, scores) < 0.06
    bins = reliability_bins(labels, scores)
    assert sum(bin_["count"] for bin_ in bins) == 100
    assert {bin_["observed_rate"] for bin_ in bins} == {0.0, 1.0}


def test_bootstrap_is_deterministic_and_ordered() -> None:
    first = bootstrap_ci(LABELS, SCORES, average_precision, resamples=100)
    second = bootstrap_ci(LABELS, SCORES, average_precision, resamples=100)
    assert first == second
    assert first["lower"] <= first["upper"]
    assert first["resamples"] > 0


def test_paired_delta_favours_the_better_ranking() -> None:
    worse = list(reversed(SCORES))
    delta = paired_bootstrap_delta(LABELS, SCORES, worse, average_precision, resamples=200)
    assert delta["upper"] > 0
    assert delta["upper"] >= delta["lower"]


def test_evaluate_exposes_the_new_fields() -> None:
    metrics = evaluate(LABELS, SCORES, 0.5)
    for key in (
        "roc_auc",
        "precision_at_10pct",
        "recall_at_10pct",
        "expected_calibration_error",
    ):
        assert key in metrics


def test_pipeline_writes_ablation_and_bootstrap(isolated_paths: dict[str, Path]) -> None:
    import json

    from meshshield.core import pipeline

    pipeline.generate_dataset(count=400, seed=11)
    metrics = pipeline.train_and_evaluate()
    assert metrics["ablation"]["graph_full"]["roc_auc"] >= 0.0
    assert "graph_only" in metrics["ablation"]
    assert metrics["evaluation_extras"]["bootstrap_95pct"]["delta_pr_auc_graph_minus_non_graph"][
        "resamples"
    ] > 0
    ablation = json.loads((isolated_paths["data"] / "ablation.json").read_text(encoding="utf-8"))
    assert ablation["model"] == "logistic"
    assert "features" in ablation["groups"]["transaction_only"]
