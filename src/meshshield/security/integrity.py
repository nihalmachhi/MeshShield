"""The integrity gate: signatures, replay window, key status and clock skew.

This module composes the controls that decide whether a delivered event may
enter the pipeline. It is deliberately separate from the model: a failed check
is a factual finding, not a probability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from statistics import median

from meshshield.core.domain import Transaction, parse_timestamp
from meshshield.security.crypto import (
    KeyRegistry,
    KeyStatus,
    signable,
)

BLOCKING_FINDINGS = frozenset(
    {
        "signature_invalid",
        "signature_reused",
        "key_revoked",
        "key_unknown",
        "key_expired",
        "key_not_yet_valid",
        "replayed_device_counter",
        "device_counter_regressed",
        "event_time_in_future",
        "duplicate_transaction_id",
        "replayed_event_id",
        "invalid_transaction_fields",
    }
)


@dataclass(frozen=True)
class IntegrityReport:
    """Outcome of inspecting one transaction."""

    accepted: bool
    findings: tuple[str, ...] = ()
    late_arrival_minutes: int = 0

    @property
    def blocking(self) -> tuple[str, ...]:
        return tuple(item for item in self.findings if item in BLOCKING_FINDINGS)


class ReplayWindow:
    """Per-device monotonic counter. Equal or lower counters are replays."""

    def __init__(self) -> None:
        self._last_counter: dict[str, int] = {}

    def check(self, device_id: str, counter: int) -> list[str]:
        """Return findings without advancing the window."""
        last = self._last_counter.get(device_id)
        if last is None:
            return []
        if counter == last:
            return ["replayed_device_counter"]
        if counter < last:
            return ["device_counter_regressed"]
        return []

    def advance(self, device_id: str, counter: int) -> None:
        """Record a counter after the event has been accepted."""
        last = self._last_counter.get(device_id)
        if last is None or counter > last:
            self._last_counter[device_id] = counter

    def last_seen(self, device_id: str) -> int | None:
        return self._last_counter.get(device_id)


class SignatureLedger:
    """Detect one signature being replayed onto a different event."""

    def __init__(self) -> None:
        self._owner: dict[str, str] = {}

    def check(self, signature: str, event_id: str) -> list[str]:
        if not signature:
            return []
        owner = self._owner.get(signature)
        return ["signature_reused"] if owner is not None and owner != event_id else []

    def record(self, signature: str, event_id: str) -> None:
        if signature:
            self._owner.setdefault(signature, event_id)


@dataclass
class ClockSkewEstimator:
    """Estimate each device's clock offset from ``ingestion_time - event_time``.

    The estimate is a rolling median of recent observations. A device that
    suddenly drifts further than ``threshold_minutes`` from its own history is
    flagged, but that flag does not block the event: skew is a quality problem,
    not proof of fraud.
    """

    threshold_minutes: float = 15.0
    window: int = 50
    _samples: dict[str, list[float]] = field(default_factory=dict)

    def observed_offset_minutes(self, tx: Transaction) -> float:
        return (
            parse_timestamp(tx.ingestion_time) - parse_timestamp(tx.event_time)
        ).total_seconds() / 60

    def check(self, tx: Transaction) -> list[str]:
        findings: list[str] = []
        offset = self.observed_offset_minutes(tx)
        if offset < 0:
            findings.append("event_time_in_future")
        history = self._samples.get(tx.device_id, [])
        if len(history) >= 5:
            baseline = median(history)
            if abs(offset - baseline) > self.threshold_minutes:
                findings.append("device_clock_drift")
        return findings

    def observe(self, tx: Transaction) -> None:
        samples = self._samples.setdefault(tx.device_id, [])
        samples.append(self.observed_offset_minutes(tx))
        if len(samples) > self.window:
            del samples[0]

    def baseline_minutes(self, device_id: str) -> float | None:
        history = self._samples.get(device_id, [])
        return median(history) if history else None


class IntegrityGate:
    """Stateful admission control for delivered transactions."""

    def __init__(
        self,
        registry: KeyRegistry | None = None,
        replay_window: ReplayWindow | None = None,
        ledger: SignatureLedger | None = None,
        skew: ClockSkewEstimator | None = None,
        late_threshold_minutes: int = 120,
    ) -> None:
        self.registry = registry
        self.replay = replay_window or ReplayWindow()
        self.ledger = ledger or SignatureLedger()
        self.skew = skew or ClockSkewEstimator()
        self.late_threshold_minutes = late_threshold_minutes
        self.seen_transaction_ids: set[str] = set()
        self.seen_event_ids: set[str] = set()

    def inspect(self, tx: Transaction) -> IntegrityReport:
        findings: list[str] = []
        arrived_at = parse_timestamp(tx.ingestion_time)
        arrived = arrived_at.astimezone(UTC)

        if tx.transaction_id in self.seen_transaction_ids:
            findings.append("duplicate_transaction_id")
        if tx.event_id in self.seen_event_ids:
            findings.append("replayed_event_id")

        if tx.key_id and self.registry is not None:
            record = self.registry.get(tx.key_id)
            status = self.registry.status(tx.key_id, arrived)
            if status is KeyStatus.UNKNOWN:
                findings.append("key_unknown")
            elif status is KeyStatus.REVOKED:
                revoked_at = record.revoked_at if record is not None else None
                signed_before = revoked_at is not None and (
                    parse_timestamp(tx.event_time) < revoked_at
                )
                findings.append("late_after_revocation" if signed_before else "key_revoked")
            elif status is KeyStatus.EXPIRED:
                findings.append("key_expired")
            elif status is KeyStatus.NOT_YET_VALID:
                findings.append("key_not_yet_valid")
            elif tx.signature and not self.registry.verify(tx.key_id, signable(tx), tx.signature):
                findings.append("signature_invalid")
            if tx.signature:
                findings.extend(self.ledger.check(tx.signature, tx.event_id))

        findings.extend(self.replay.check(tx.device_id, tx.device_counter))
        findings.extend(self.skew.check(tx))

        delay = int((arrived_at - parse_timestamp(tx.event_time)).total_seconds() // 60)
        late = max(delay, 0)
        if late > self.late_threshold_minutes:
            findings.append("late_arrival")

        accepted = not any(item in BLOCKING_FINDINGS for item in findings)
        if accepted:
            self.seen_transaction_ids.add(tx.transaction_id)
            self.seen_event_ids.add(tx.event_id)
            self.replay.advance(tx.device_id, tx.device_counter)
            self.ledger.record(tx.signature, tx.event_id)
            self.skew.observe(tx)
        unique = tuple(dict.fromkeys(findings))
        return IntegrityReport(accepted=accepted, findings=unique, late_arrival_minutes=late)

    def inspect_many(self, transactions: list[Transaction]) -> list[IntegrityReport]:
        """Inspect in delivery order, which is the order a reviewer would see."""
        ordered = sorted(
            transactions,
            key=lambda tx: (parse_timestamp(tx.ingestion_time), tx.transaction_id),
        )
        return [self.inspect(tx) for tx in ordered]


class TamperKind:
    """The tamper patterns the synthetic generator can produce."""

    BYTE_FLIP = "byte_flip"
    AMOUNT_SWAP = "amount_swap"
    SIGNATURE_REUSE = "signature_reuse"


def sign_time(tx: Transaction) -> datetime:
    """The timestamp a key status must be evaluated against (arrival, not event)."""
    return parse_timestamp(tx.ingestion_time)
