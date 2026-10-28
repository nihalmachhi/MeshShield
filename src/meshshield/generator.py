"""Seeded generator for explicitly synthetic payment and sync events."""

import random
from datetime import UTC, datetime, timedelta

from meshshield.domain import SyncEvent, Transaction

SCENARIOS = ("normal", "high_amount", "shared_device", "replay_attempt", "invalid_signature")


def generate(count: int, seed: int, start: datetime | None = None) -> tuple[list[Transaction], list[SyncEvent]]:
    if count < 100:
        raise ValueError("Generate at least 100 transactions for a meaningful time split.")
    rng = random.Random(seed)
    origin = start or datetime(2025, 1, 1, tzinfo=UTC)
    accounts = [f"acct_{i:04d}" for i in range(240)]
    devices = [f"device_{i:04d}" for i in range(200)]
    merchants = [f"merchant_{i:03d}" for i in range(45)]
    hub_devices = devices[:8]
    account_device: dict[str, str] = {}
    transactions: list[Transaction] = []
    events: list[SyncEvent] = []
    for index in range(count):
        account = rng.choice(accounts)
        scenario = rng.choices(SCENARIOS, weights=(84, 4, 5, 3, 4), k=1)[0]
        if scenario == "shared_device":
            device = rng.choice(hub_devices)
        else:
            device = account_device.setdefault(account, rng.choice(devices))
        event_at = origin + timedelta(minutes=index * 8 + rng.randrange(8))
        amount = round(min(rng.lognormvariate(3.05, 0.8), 850.0), 2)
        signature_valid = scenario != "invalid_signature"
        if scenario == "high_amount":
            amount = round(rng.uniform(250, 950), 2)
        if scenario in ("replay_attempt", "invalid_signature"):
            amount = round(rng.uniform(120, 700), 2)
        delayed = rng.random() < 0.22 or scenario == "replay_attempt"
        offline_minutes = rng.randint(20, 600) if delayed else rng.randint(0, 12)
        ingested_at = event_at + timedelta(minutes=offline_minutes)
        tx_id = f"txn_{index:07d}"
        event_id = f"evt_{index:07d}"
        if scenario == "replay_attempt" and events:
            event_id = rng.choice(events).event_id
            if rng.random() < 0.25:
                signature_valid = False
        transactions.append(Transaction(
            transaction_id=tx_id, account_id=account, device_id=device,
            merchant_id=rng.choice(merchants), amount=amount, currency="USD",
            event_time=event_at.isoformat().replace("+00:00", "Z"),
            ingestion_time=ingested_at.isoformat().replace("+00:00", "Z"),
            offline_duration_minutes=offline_minutes, signature_valid=signature_valid,
            event_id=event_id,
            label=int(scenario != "normal"), scenario=scenario,
        ))
        events.append(SyncEvent(event_id, tx_id, transactions[-1].event_time,
                                transactions[-1].ingestion_time, "synthetic-device", index,
                                signature_valid))
    return transactions, events
