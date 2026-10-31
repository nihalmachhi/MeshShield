"""The README claims point-in-time features. These tests make that falsifiable."""

from __future__ import annotations

import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from meshshield.core.domain import Transaction, parse_timestamp
from meshshield.data.generator import generate
from meshshield.features.build import build_features


@pytest.fixture(scope="module")
def sample() -> list[Transaction]:
    transactions, _ = generate(240, seed=11)
    return transactions


def _features_from_past(
    all_transactions: list[Transaction], target: Transaction
) -> dict[str, float]:
    """Recompute one row using strictly earlier events plus the target itself."""
    target_time = parse_timestamp(target.event_time)
    earlier = [tx for tx in all_transactions if parse_timestamp(tx.event_time) < target_time]
    return build_features([*earlier, target])[target.transaction_id]


def test_features_equal_a_strictly_causal_recompute(sample: list[Transaction]) -> None:
    full = build_features(sample)
    for target in sample[::7]:
        assert full[target.transaction_id] == _features_from_past(sample, target), (
            f"{target.transaction_id} depends on events at or after its own event time"
        )


@pytest.mark.parametrize("shuffle_seed", range(5))
def test_shuffling_arrival_order_does_not_change_features(
    sample: list[Transaction], shuffle_seed: int
) -> None:
    shuffled = list(sample)
    random.Random(shuffle_seed).shuffle(shuffled)
    assert build_features(shuffled) == build_features(sample)


@given(st.integers(min_value=0, max_value=500))
@settings(max_examples=15, deadline=None)
def test_hypothesis_shuffle_keeps_every_row(seed: int) -> None:
    transactions, _ = generate(160, seed=seed)
    reference = build_features(transactions)
    shuffled = list(transactions)
    random.Random(seed).shuffle(shuffled)
    assert build_features(shuffled) == reference


def test_a_future_event_cannot_rewrite_history(sample: list[Transaction]) -> None:
    before = build_features(sample)
    later = max(sample, key=lambda tx: parse_timestamp(tx.event_time))
    extra = Transaction(
        transaction_id="txn_future_probe",
        account_id=later.account_id,
        device_id=later.device_id,
        merchant_id=later.merchant_id,
        amount=999.0,
        currency="USD",
        event_time=later.event_time.replace("2025", "2026"),
        ingestion_time=later.event_time.replace("2025", "2026"),
        offline_duration_minutes=0,
        signature_valid=True,
        event_id="evt_future_probe",
        label=1,
        scenario="future_probe",
    )
    after = build_features([*sample, extra])
    for transaction_id, row in before.items():
        assert after[transaction_id] == row, f"{transaction_id} changed after a later event arrived"


def test_only_earlier_events_are_visible_at_equal_timestamps() -> None:
    from datetime import UTC, datetime

    from conftest import make_transaction

    moment = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    first = make_transaction(0, account_id="acct_a", event_time=moment)
    second = make_transaction(1, account_id="acct_a", event_time=moment)
    rows = build_features([first, second])
    assert rows[first.transaction_id]["account_velocity_1h"] == 0.0
    assert rows[second.transaction_id]["account_velocity_1h"] == 0.0
