"""The holdout must be strictly later than training, and labels must never be features."""

from __future__ import annotations

import pytest

from meshshield.config import FEATURES, GRAPH_FEATURES
from meshshield.core.domain import parse_timestamp
from meshshield.core.pipeline import split_chronologically
from meshshield.data.generator import generate
from meshshield.eval.metrics import split_index
from meshshield.features.build import vector


def test_split_is_strictly_chronological() -> None:
    transactions, _ = generate(400, seed=21)
    train, test = split_chronologically(transactions)

    assert len(train) + len(test) == len(transactions)
    assert len(train) == 320 and len(test) == 80
    latest_train = max(parse_timestamp(tx.event_time) for tx in train)
    earliest_test = min(parse_timestamp(tx.event_time) for tx in test)
    assert latest_train < earliest_test


def test_split_sizes_are_eighty_twenty() -> None:
    transactions, _ = generate(200, seed=22)
    train, test = split_chronologically(transactions)
    assert len(train) == split_index(len(transactions))
    assert abs(len(train) / len(transactions) - 0.8) < 0.01
    assert len(train) > 0 and len(test) > 0


@pytest.mark.parametrize("name", FEATURES)
def test_no_feature_is_a_label_or_identifier(name: str) -> None:
    forbidden = {"label", "scenario", "transaction_id", "event_id", "signature_valid"}
    assert name not in forbidden
    assert "label" not in name


def test_feature_vector_is_only_the_contract() -> None:
    row = {name: 1.0 for name in GRAPH_FEATURES}
    assert len(vector(row)) == len(GRAPH_FEATURES)
    assert len(vector(row, graph=False)) == len(FEATURES)
    assert vector({"amount": 999.0, "label": 1}) == [0.0] * len(GRAPH_FEATURES)


def test_split_boundary_events_are_not_shared() -> None:
    transactions, _ = generate(120, seed=23)
    train, test = split_chronologically(transactions)
    train_ids = {tx.transaction_id for tx in train}
    test_ids = {tx.transaction_id for tx in test}
    assert train_ids.isdisjoint(test_ids)
