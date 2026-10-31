"""The public-data evaluator must work on any permitted labelled CSV."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from meshshield.data.generator import generate
from meshshield.eval.public import evaluate_public


def test_public_evaluator_reports_real_holdout_metrics() -> None:
    transactions, _ = generate(400, seed=31, profile="easy")
    # Public adapters set every delay to zero; mirror that so the test measures
    # the evaluator rather than offline-sync features the data will not have.
    transactions = [
        replace(tx, offline_duration_minutes=0) for tx in transactions
    ]
    result = evaluate_public(transactions)
    assert result["dataset"]["rows"] == 400
    assert result["dataset"]["test"] == 80
    assert 0.0 <= result["graph_model"]["pr_auc_average_precision"] <= 1.0
    assert 0.0 <= result["non_graph_model"]["roc_auc"] <= 1.0
    assert math.isfinite(result["threshold"])
    assert "not comparable" in result["note"]


def test_public_evaluator_rejects_a_tiny_or_single_class_file() -> None:
    transactions, _ = generate(120, seed=3)
    with pytest.raises(ValueError, match="at least 100"):
        evaluate_public(transactions[:50])
    negatives = [replace(tx, label=0) for tx in transactions]
    with pytest.raises(ValueError, match="no positive labels"):
        evaluate_public(negatives)
