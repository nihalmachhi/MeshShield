"""Signature, replay-window, key-status, tamper and clock-skew controls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from conftest import make_transaction

from meshshield.core.domain import Transaction
from meshshield.security.crypto import (
    Ed25519Signer,
    KeyRegistry,
    KeyStatus,
    SimulatedSigner,
    canonical_payload,
    payload_digest,
    signable,
    tamper_bytes,
)
from meshshield.security.integrity import (
    ClockSkewEstimator,
    IntegrityGate,
    ReplayWindow,
    SignatureLedger,
)

T0 = datetime(2025, 1, 1, tzinfo=UTC)


def signed(
    signer: SimulatedSigner,
    index: int = 0,
    *,
    device_id: str = "device_0001",
    amount: float = 50.0,
    **extra: object,
) -> Transaction:
    tx = make_transaction(index, device_id=device_id, amount=amount, **extra)
    tx = Transaction(**{**tx.to_dict(), "key_id": signer.key_id})
    return Transaction(**{**tx.to_dict(), "signature": signer.sign(signable(tx))})


def registry_for(signer: SimulatedSigner) -> KeyRegistry:
    registry = KeyRegistry()
    registry.register(signer, valid_from=T0, device_id="device_0001")
    return registry


# --------------------------------------------------------------------------- #
# Canonical bytes and signers
# --------------------------------------------------------------------------- #


def test_canonical_bytes_ignore_key_order() -> None:
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}
    assert canonical_payload(left) == canonical_payload(right)
    assert payload_digest(left) == payload_digest(right)
    assert b'{"a":1,"b":2}' == canonical_payload(left)


def test_simulated_signer_round_trips_and_detects_a_flip() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    payload = {"event_id": "e1", "amount": 10}
    signature = signer.sign(payload)
    assert signer.verify(payload, signature)
    assert not signer.verify({**payload, "amount": 11}, signature)
    assert not signer.verify(payload, tamper_bytes(signature))


def test_ed25519_round_trip() -> None:
    cryptography = pytest.importorskip("cryptography")
    del cryptography
    signer = Ed25519Signer.generate("ed-key-1")
    payload = {"event_id": "e1", "amount": 10}
    signature = signer.sign(payload)
    assert signer.verify(payload, signature)
    assert not signer.verify({**payload, "amount": 11}, signature)
    assert not signer.verify(payload, "not-base64")


def test_key_registry_status_windows() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    registry = KeyRegistry()
    registry.register(
        signer,
        valid_from=T0,
        valid_to=T0 + timedelta(hours=2),
        revoked_at=T0 + timedelta(hours=1),
    )
    assert registry.status(signer.key_id, T0 - timedelta(minutes=1)) is KeyStatus.NOT_YET_VALID
    assert registry.status(signer.key_id, T0 + timedelta(minutes=30)) is KeyStatus.VALID
    assert registry.status(signer.key_id, T0 + timedelta(minutes=90)) is KeyStatus.REVOKED
    assert registry.status("missing", T0) is KeyStatus.UNKNOWN


def test_rotation_closes_the_old_key_window() -> None:
    old = SimulatedSigner.for_device("device_0001")
    new = SimulatedSigner.for_device("device_0001", key_id="device_0001-sim-2")
    registry = registry_for(old)
    registry.rotate(old.key_id, new, T0 + timedelta(hours=1))

    assert registry.status(old.key_id, T0 + timedelta(minutes=59)) is KeyStatus.VALID
    assert registry.status(old.key_id, T0 + timedelta(hours=1)) is KeyStatus.EXPIRED
    assert registry.status(new.key_id, T0 + timedelta(hours=1)) is KeyStatus.VALID


# --------------------------------------------------------------------------- #
# Replay window and signature ledger
# --------------------------------------------------------------------------- #


def test_replay_window_rejects_equal_and_backwards_counters() -> None:
    window = ReplayWindow()
    assert window.check("d1", 1) == []
    window.advance("d1", 5)
    assert window.check("d1", 5) == ["replayed_device_counter"]
    assert window.check("d1", 4) == ["device_counter_regressed"]
    assert window.check("d1", 6) == []
    assert window.last_seen("d1") == 5


def test_signature_reuse_is_detected_across_event_ids() -> None:
    ledger = SignatureLedger()
    ledger.record("sig-abc", "evt_1")
    assert ledger.check("sig-abc", "evt_1") == []
    assert ledger.check("sig-abc", "evt_2") == ["signature_reused"]


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #


def test_a_valid_signed_transaction_is_accepted() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    gate = IntegrityGate(registry=registry_for(signer))
    report = gate.inspect(signed(signer))
    assert report.accepted is True
    assert report.findings == ()


def test_a_tampered_amount_is_rejected() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    gate = IntegrityGate(registry=registry_for(signer))
    good = signed(signer)
    tampered = Transaction(**{**good.to_dict(), "amount": good.amount + 900})
    report = gate.inspect(tampered)
    assert report.accepted is False
    assert "signature_invalid" in report.findings


def test_a_replayed_counter_is_rejected() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    gate = IntegrityGate(registry=registry_for(signer))
    first = signed(signer, 0, device_counter=1)
    replay = signed(signer, 1, device_counter=1)
    assert gate.inspect(first).accepted is True
    report = gate.inspect(replay)
    assert report.accepted is False
    assert "replayed_device_counter" in report.findings


def test_a_revoked_key_is_rejected_after_the_revocation() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    registry = KeyRegistry()
    registry.register(
        signer,
        valid_from=T0,
        revoked_at=T0 + timedelta(hours=1),
        device_id="device_0001",
    )
    gate = IntegrityGate(registry=registry)
    tx = signed(
        signer,
        event_time=T0 + timedelta(hours=2),
        ingestion_time=T0 + timedelta(hours=2, minutes=5),
    )
    report = gate.inspect(tx)
    assert report.accepted is False
    assert "key_revoked" in report.findings


def test_a_signature_made_before_revocation_but_arriving_late_is_flagged_not_blocked() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    registry = KeyRegistry()
    registry.register(
        signer,
        valid_from=T0,
        revoked_at=T0 + timedelta(hours=1),
        device_id="device_0001",
    )
    gate = IntegrityGate(registry=registry)
    tx = signed(
        signer,
        event_time=T0 + timedelta(minutes=30),
        ingestion_time=T0 + timedelta(hours=4),
    )
    report = gate.inspect(tx)
    assert report.accepted is True
    assert "late_after_revocation" in report.findings
    assert "late_arrival" in report.findings
    assert report.late_arrival_minutes == 210


def test_unknown_key_is_rejected() -> None:
    signer = SimulatedSigner.for_device("device_0001")
    gate = IntegrityGate(registry=KeyRegistry())
    report = gate.inspect(signed(signer))
    assert report.accepted is False
    assert "key_unknown" in report.findings


def test_the_gate_applies_to_generated_data() -> None:
    from meshshield.data.generator import generate

    transactions, _ = generate(120, seed=4)
    signer_registry = KeyRegistry()
    for device in sorted({tx.device_id for tx in transactions}):
        signer_registry.register(
            SimulatedSigner.for_device(device), valid_from=T0 - timedelta(days=30), device_id=device
        )
    gate = IntegrityGate(registry=signer_registry)
    reports = gate.inspect_many(transactions)
    assert len(reports) == len(transactions)
    assert sum(report.accepted for report in reports) > 80


# --------------------------------------------------------------------------- #
# Clock skew
# --------------------------------------------------------------------------- #


def test_event_time_in_the_future_is_blocking() -> None:
    estimator = ClockSkewEstimator()
    tx = make_transaction(1, event_time=T0 + timedelta(minutes=10), ingestion_time=T0)
    tx = Transaction(**{**tx.to_dict(), "offline_duration_minutes": 0})
    assert "event_time_in_future" in estimator.check(tx)


def test_drift_is_flagged_against_the_devices_own_history() -> None:
    estimator = ClockSkewEstimator(threshold_minutes=15.0)
    for index in range(6):
        estimator.observe(
            make_transaction(
                index,
                event_time=T0 + timedelta(minutes=index * 10),
                ingestion_time=T0 + timedelta(minutes=index * 10 + 5),
            )
        )
    drifted = make_transaction(
        99,
        event_time=T0 + timedelta(minutes=200),
        ingestion_time=T0 + timedelta(minutes=260),
    )
    assert "device_clock_drift" in estimator.check(drifted)
    assert estimator.baseline_minutes("device_0001") == pytest.approx(5.0)
