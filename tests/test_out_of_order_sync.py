"""Delivery order must not change what the system believes happened."""

from __future__ import annotations

import random
from pathlib import Path

from conftest import make_transaction

from meshshield.data.generator import generate
from meshshield.data.storage import IdempotencyStore
from meshshield.features.build import build_features
from meshshield.sync.simulator import flag_late_arrivals, process_delivery, simulate_delivery


def test_in_order_and_shuffled_delivery_accept_the_same_events(tmp_path: Path) -> None:
    transactions, events = generate(200, seed=3)
    store_a = IdempotencyStore(tmp_path / "a.sqlite3")
    ordered = process_delivery(events, store_a)
    store_a.close()

    shuffled = list(events)
    random.Random(99).shuffle(shuffled)
    store_b = IdempotencyStore(tmp_path / "b.sqlite3")
    out_of_order = process_delivery(shuffled, store_b)
    store_b.close()

    assert ordered["accepted"] == out_of_order["accepted"]
    assert ordered["duplicate_deliveries_ignored"] == out_of_order["duplicate_deliveries_ignored"]
    assert build_features(transactions) == build_features(list(reversed(transactions)))


def test_a_duplicate_batch_counts_once(tmp_path: Path) -> None:
    _, events = generate(120, seed=5)
    store_d = IdempotencyStore(tmp_path / "d.sqlite3")
    summary = process_delivery(simulate_delivery(events), store_d)
    store_d.close()
    assert summary["delivered"] == (
        summary["accepted"]
        + summary["duplicate_deliveries_ignored"]
        + summary["invalid_signatures_rejected"]
    )
    assert summary["duplicate_deliveries_ignored"] > 0


def test_late_arrival_is_flagged_but_does_not_change_history() -> None:
    transactions, _ = generate(160, seed=8)
    baseline = build_features(transactions)
    late = flag_late_arrivals(transactions, threshold_minutes=60)
    assert late, "the generator should produce at least one late sync"
    assert build_features(list(reversed(transactions))) == baseline

    very_late = make_transaction(
        999,
        event_time="2025-01-01T00:00:00Z",
        ingestion_time="2025-01-01T09:00:00Z",
        offline_duration_minutes=540,
    )
    assert flag_late_arrivals([very_late], threshold_minutes=60) == {"txn_0000999": 540}
