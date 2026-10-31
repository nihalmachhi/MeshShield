"""Device clocks are skewed and drifting; the policy must be explicit and tested."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from conftest import make_transaction

from meshshield.core.domain import Transaction
from meshshield.data.generator import generate
from meshshield.security.integrity import ClockSkewEstimator, IntegrityGate

T0 = datetime(2025, 1, 1, tzinfo=UTC)


def test_each_device_keeps_its_own_offset() -> None:
    transactions, _ = generate(240, seed=13)
    offsets: dict[str, list[float]] = {}
    for tx in transactions:
        offsets.setdefault(tx.device_id, []).append(tx.clock_offset_seconds)

    assert len(offsets) > 20
    # Offsets are per device, not per transaction: the drift term is small.
    for device, values in offsets.items():
        spread = max(values) - min(values)
        assert spread < 60.0, f"{device} offset moved by {spread}s inside one run"
    assert len({round(values[0], 1) for values in offsets.values()}) > 5


def test_offsets_are_reproducible() -> None:
    first, _ = generate(160, seed=21)
    second, _ = generate(160, seed=21)
    assert [tx.clock_offset_seconds for tx in first] == [tx.clock_offset_seconds for tx in second]


def test_an_event_from_the_future_is_blocking() -> None:
    gate = IntegrityGate()
    tx = make_transaction(
        1,
        event_time=T0 + timedelta(minutes=5),
        ingestion_time=T0,
        offline_duration_minutes=0,
    )
    report = gate.inspect(tx)
    assert report.accepted is False
    assert "event_time_in_future" in report.findings


def test_estimator_learns_a_stable_offset() -> None:
    estimator = ClockSkewEstimator(threshold_minutes=10.0)
    for index in range(8):
        estimator.observe(
            make_transaction(
                index,
                event_time=T0 + timedelta(minutes=index * 5),
                ingestion_time=T0 + timedelta(minutes=index * 5 + 3),
            )
        )
    assert estimator.baseline_minutes("device_0001") == 3.0


def test_a_far_late_sync_is_flagged_not_rejected() -> None:
    gate = IntegrityGate(late_threshold_minutes=60)
    tx = make_transaction(
        2,
        event_time=T0,
        ingestion_time=T0 + timedelta(hours=5),
        offline_duration_minutes=300,
    )
    report = gate.inspect(tx)
    assert report.accepted is True
    assert "late_arrival" in report.findings
    assert report.late_arrival_minutes == 300


def test_contract_bounds_the_skew_window() -> None:
    tx = make_transaction(
        3,
        event_time=T0 + timedelta(minutes=30),
        ingestion_time=T0,
        offline_duration_minutes=0,
    )
    try:
        tx.validate()
    except ValueError as exc:
        assert "implausibly far ahead" in str(exc)
    else:  # pragma: no cover - the contract must reject this
        raise AssertionError("a 30 minute future timestamp should not validate")


def test_a_transaction_can_round_trip_with_clock_fields() -> None:
    tx = make_transaction(4)
    restored = Transaction.from_dict(
        {**tx.to_dict(), "clock_offset_seconds": -1.25, "device_counter": 7}
    )
    assert restored.clock_offset_seconds == -1.25
    assert restored.device_counter == 7
