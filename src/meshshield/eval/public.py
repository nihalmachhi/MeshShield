"""Evaluate the same pipeline on an external, permitted public dataset.

Nothing here is tuned on the public data and no result is hard-coded: the scores
come from the rows the caller supplies. PaySim and IEEE-CIS are read through the
adapters in :mod:`meshshield.data.public_datasets`; any other CSV can be mapped
with the adapter's required columns.
"""

from __future__ import annotations

from typing import Any

from meshshield.config import (
    FALSE_NEGATIVE_COST,
    FALSE_POSITIVE_COST,
    FEATURES,
    GRAPH_FEATURES,
    REVIEW_CAPACITY,
)
from meshshield.core.domain import Transaction, parse_timestamp
from meshshield.core.pipeline import split_chronologically
from meshshield.eval.calibration import fit_platt, select_cost_threshold
from meshshield.eval.metrics import evaluate, split_index
from meshshield.features.build import build_features, vector
from meshshield.models.registry import create_model


def evaluate_public(
    transactions: list[Transaction],
    *,
    model_name: str = "logistic",
    train_fraction: float = 0.8,
) -> dict[str, Any]:
    """Train on the earliest rows and report holdout metrics for two feature sets."""
    if len(transactions) < 100:
        raise ValueError("need at least 100 rows for a chronological holdout")
    if not any(tx.label == 1 for tx in transactions):
        raise ValueError("the dataset has no positive labels, so it cannot be evaluated")
    ordered = sorted(
        transactions, key=lambda tx: (parse_timestamp(tx.event_time), tx.transaction_id)
    )
    features = build_features(ordered)
    train, test = split_chronologically(ordered, train_fraction)
    calibration_cut = split_index(len(train), 0.8)
    fit_rows, calibration = train[:calibration_cut], train[calibration_cut:]
    labels_fit = [int(tx.label or 0) for tx in fit_rows]
    if len(set(labels_fit)) < 2:
        raise ValueError("the training slice needs both classes for a supervised model")
    graph_model = create_model(
        model_name,
        [vector(features[tx.transaction_id]) for tx in fit_rows],
        labels_fit,
        GRAPH_FEATURES,
    )
    base_model = create_model(
        model_name,
        [vector(features[tx.transaction_id], graph=False) for tx in fit_rows],
        labels_fit,
        FEATURES,
    )
    labels_calibration = [int(tx.label or 0) for tx in calibration]
    calibration_scores = [
        graph_model.score(vector(features[tx.transaction_id])) for tx in calibration
    ]
    threshold: float = 0.5
    if len(set(labels_calibration)) == 2:
        calibrator = fit_platt(calibration_scores, labels_calibration)
        policy = select_cost_threshold(
            labels_calibration,
            [calibrator.apply(score) for score in calibration_scores],
            FALSE_POSITIVE_COST,
            FALSE_NEGATIVE_COST,
            REVIEW_CAPACITY,
        )
        threshold = float(policy["threshold"])
        calibrated_test = [
            calibrator.apply(graph_model.score(vector(features[tx.transaction_id])))
            for tx in test
        ]
    else:
        calibrated_test = [
            graph_model.score(vector(features[tx.transaction_id])) for tx in test
        ]
    labels_test = [int(tx.label or 0) for tx in test]
    return {
        "dataset": {
            "name": "public_dataset",
            "rows": len(ordered),
            "train": len(train),
            "test": len(test),
            "positives": sum(labels_test),
            "positive_rate": sum(labels_test) / len(labels_test),
            "split": "event-time chronological holdout",
        },
        "model": model_name,
        "graph_model": evaluate(
            labels_test,
            [graph_model.score(vector(features[tx.transaction_id])) for tx in test],
        ),
        "graph_model_calibrated": evaluate(labels_test, calibrated_test, threshold),
        "non_graph_model": evaluate(
            labels_test,
            [base_model.score(vector(features[tx.transaction_id], graph=False)) for tx in test],
        ),
        "threshold": threshold,
        "note": (
            "Public datasets differ from the synthetic generator in label meaning, "
            "sampling and missing devices. These numbers are not comparable to the "
            "synthetic results and are not a claim about production fraud detection."
        ),
    }
