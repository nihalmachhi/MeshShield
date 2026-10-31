"""Integrity findings are deterministic checks, separate from any model score."""

from __future__ import annotations

import pytest
from conftest import make_event, make_transaction

from meshshield.core.domain import Transaction
from meshshield.security.rules import inspect_event_order, inspect_transaction


def test_bad_signature_is_reported() -> None:
    tx = make_transaction(1, signature_valid=False)
    assert inspect_transaction(tx) == ["invalid_simulated_signature"]


def test_duplicate_transaction_id_is_reported() -> None:
    tx = make_transaction(2)
    findings = inspect_transaction(tx, seen_transaction_ids={tx.transaction_id})
    assert "duplicate_transaction_id" in findings


def test_replayed_event_id_is_reported() -> None:
    tx = make_transaction(3)
    findings = inspect_transaction(tx, seen_event_ids={tx.event_id})
    assert "replayed_event_id" in findings


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("amount", 0.0, "amount must be positive"),
        ("offline_duration_minutes", -1, "offline duration cannot be negative"),
        ("label", 2, "label must be 0, 1, or null"),
    ],
)
def test_impossible_fields_are_rejected(field: str, value: object, message: str) -> None:
    tx = make_transaction(4)
    broken = Transaction(**{**tx.to_dict(), field: value})
    with pytest.raises(ValueError, match=message):
        broken.validate()


def test_naive_timestamps_are_rejected() -> None:
    tx = make_transaction(5, event_time="2025-01-01T00:00:00", ingestion_time="2025-01-01T00:10:00")
    with pytest.raises(ValueError, match="timezone"):
        tx.validate()


def test_ingestion_before_event_time_is_rejected() -> None:
    tx = make_transaction(
        6, event_time="2025-01-01T10:00:00Z", ingestion_time="2025-01-01T09:00:00Z"
    )
    with pytest.raises(ValueError, match="ingestion_time"):
        tx.validate()


def test_event_order_findings_cover_sequence_and_regression() -> None:
    first = make_event(1)
    second = make_event(2)
    reversed_time = make_event(3, event_time="2025-01-01T00:00:00Z")
    findings = inspect_event_order([first, second, reversed_time])
    assert "event_time_regressed_with_sequence" in findings

    duplicate_sequence = make_event(1)
    findings = inspect_event_order([first, duplicate_sequence])
    assert "duplicate_sequence" in findings
