"""Seeded generator for explicitly synthetic payment and sync events.

Every device gets its own simulated key and its own clock model: a fixed offset
plus a slow drift. The recorded ``event_time`` is the device clock, never the
true time, which is what makes clock-skew handling testable.

Profiles
--------
``easy``
    The original generator: independent scenarios drawn from fixed weights.
``hard``
    Adversarial scenarios: fraud rings, slow-burn accounts, structuring just
    under the amount rule, device rotation and label noise. Added in this module
    rather than a separate file so both profiles share the same contracts.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from meshshield.core.domain import SyncEvent, Transaction
from meshshield.security.crypto import SimulatedSigner, signable, tamper_bytes

EASY_SCENARIOS = ("normal", "high_amount", "shared_device", "replay_attempt", "invalid_signature")
HARD_SCENARIOS = (
    "normal",
    "high_amount",
    "shared_device",
    "replay_attempt",
    "invalid_signature",
    "fraud_ring",
    "slow_burn",
    "structuring",
    "device_rotation",
)
PROFILES = ("easy", "hard")


@dataclass(frozen=True)
class DeviceClock:
    """A device's clock model in minutes relative to true time."""

    offset_minutes: float
    drift_ppm: float

    def time_at(self, true_time: datetime, elapsed_minutes: float) -> datetime:
        drift = self.drift_ppm * 1e-6 * elapsed_minutes
        return true_time + timedelta(minutes=self.offset_minutes + drift)


def _device_clocks(rng: random.Random, devices: list[str]) -> dict[str, DeviceClock]:
    return {
        device: DeviceClock(
            offset_minutes=rng.gauss(0.0, 2.5),
            drift_ppm=rng.uniform(-40.0, 40.0),
        )
        for device in devices
    }


def generate(
    count: int,
    seed: int,
    start: datetime | None = None,
    profile: str = "easy",
    *,
    label_noise: float = 0.0,
    benign_shared_devices: int = 8,
) -> tuple[list[Transaction], list[SyncEvent]]:
    """Generate transactions and sync events.

    The returned transactions carry a device counter and a simulated signature,
    so the integrity gate can be exercised without any optional dependency.
    """
    if count < 100:
        raise ValueError("Generate at least 100 transactions for a meaningful time split.")
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; choose one of {PROFILES}")
    if not 0.0 <= label_noise < 0.5:
        raise ValueError("label_noise must be in [0, 0.5)")

    rng = random.Random(seed)
    origin = start or datetime(2025, 1, 1, tzinfo=UTC)
    accounts = [f"acct_{i:04d}" for i in range(240)]
    devices = [f"device_{i:04d}" for i in range(200)]
    merchants = [f"merchant_{i:03d}" for i in range(45)]
    hub_devices = devices[:benign_shared_devices]
    clocks = _device_clocks(rng, devices)
    account_device: dict[str, str] = {}
    device_counters: defaultdict[str, int] = defaultdict(int)
    transactions: list[Transaction] = []
    events: list[SyncEvent] = []
    signature_pool: list[str] = []
    slow_burn_accounts = set(accounts[40:52]) if profile == "hard" else set()

    for index in range(count):
        account = rng.choice(accounts)
        scenario = _choose_scenario(rng, profile, index, slow_burn_accounts, account)
        if scenario in ("shared_device", "fraud_ring"):
            device = rng.choice(hub_devices)
        elif scenario == "device_rotation":
            device = devices[(index * 7) % len(devices)]
        else:
            device = account_device.setdefault(account, rng.choice(devices))

        true_time = origin + timedelta(minutes=index * 8 + rng.randrange(8))
        clock = clocks[device]
        device_time = clock.time_at(true_time, elapsed_minutes=index * 8)

        amount = round(min(rng.lognormvariate(3.05, 0.8), 850.0), 2)
        if scenario == "high_amount":
            amount = round(rng.uniform(250, 950), 2)
        if scenario == "structuring":
            # Deliberately just under the 250 amount rule.
            amount = round(rng.uniform(232.0, 249.0), 2)
        if scenario in ("replay_attempt", "invalid_signature", "fraud_ring"):
            amount = round(rng.uniform(120, 700), 2)

        delayed = rng.random() < 0.22 or scenario in ("replay_attempt", "slow_burn")
        offline_minutes = rng.randint(20, 600) if delayed else rng.randint(0, 12)
        ingested_at = true_time + timedelta(minutes=offline_minutes)

        tx_id = f"txn_{index:07d}"
        event_id = f"evt_{index:07d}"
        if scenario == "replay_attempt" and events:
            event_id = rng.choice(events).event_id

        device_counters[device] += 1
        transaction = Transaction(
            transaction_id=tx_id,
            account_id=account,
            device_id=device,
            merchant_id=rng.choice(merchants),
            amount=amount,
            currency="USD",
            event_time=_iso(device_time),
            ingestion_time=_iso(ingested_at),
            offline_duration_minutes=offline_minutes,
            signature_valid=True,
            event_id=event_id,
            label=int(scenario != "normal"),
            scenario=scenario,
            device_counter=device_counters[device],
            clock_offset_seconds=round((device_time - true_time).total_seconds(), 3),
        )
        transaction = _sign(transaction)
        if scenario == "invalid_signature":
            transaction = _with_signature(transaction, tamper_bytes(transaction.signature))
        elif scenario == "replay_attempt" and signature_pool and rng.random() < 0.4:
            transaction = _with_signature(transaction, rng.choice(signature_pool))
        signature_pool.append(transaction.signature)

        if label_noise and rng.random() < label_noise:
            transaction = _with_label(transaction, 1 - int(transaction.label or 0))
        transaction = _with_signature_valid(transaction, _signature_ok(transaction))
        transactions.append(transaction)
        events.append(
            SyncEvent(
                event_id=transaction.event_id,
                transaction_id=transaction.transaction_id,
                event_time=transaction.event_time,
                ingestion_time=transaction.ingestion_time,
                source="synthetic-device",
                sequence=index,
                signature_valid=transaction.signature_valid,
            )
        )
    return transactions, events


def _choose_scenario(
    rng: random.Random,
    profile: str,
    index: int,
    slow_burn_accounts: set[str],
    account: str,
) -> str:
    if profile == "easy":
        return rng.choices(EASY_SCENARIOS, weights=(84, 4, 5, 3, 4), k=1)[0]
    if account in slow_burn_accounts and index % 11 == 0:
        return "slow_burn"
    return rng.choices(
        HARD_SCENARIOS,
        weights=(62, 5, 5, 3, 3, 7, 5, 6, 4),
        k=1,
    )[0]


def _sign(tx: Transaction) -> Transaction:
    signer = SimulatedSigner.for_device(tx.device_id)
    return _replace(tx, key_id=signer.key_id, signature=signer.sign(signable(tx)))


def _signature_ok(tx: Transaction) -> bool:
    return SimulatedSigner.for_device(tx.device_id).verify(signable(tx), tx.signature)


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _replace(tx: Transaction, **changes: Any) -> Transaction:
    return Transaction(**{**tx.to_dict(), **changes})


def _with_signature(tx: Transaction, signature: str) -> Transaction:
    return _replace(tx, signature=signature)


def _with_signature_valid(tx: Transaction, valid: bool) -> Transaction:
    return _replace(tx, signature_valid=valid)


def _with_label(tx: Transaction, label: int) -> Transaction:
    return _replace(tx, label=label)
