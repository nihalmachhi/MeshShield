"""Shared builders and fixtures for the MeshShield test suite."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from meshshield.core.domain import SyncEvent, Transaction

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_TIME = datetime(2025, 1, 1, tzinfo=UTC)


def iso(moment: datetime) -> str:
    """Serialize a datetime the way the contracts expect (UTC, Z suffix)."""
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def make_transaction(
    index: int = 0,
    *,
    account_id: str | None = None,
    device_id: str = "device_0001",
    merchant_id: str = "merchant_001",
    amount: float = 50.0,
    event_time: datetime | str | None = None,
    ingestion_time: datetime | str | None = None,
    label: int = 0,
    scenario: str = "normal",
    signature_valid: bool = True,
    offline_duration_minutes: int = 5,
    transaction_id: str | None = None,
    event_id: str | None = None,
    **extra: Any,
) -> Transaction:
    """Build one valid synthetic transaction with deterministic defaults."""
    moment = (
        event_time if isinstance(event_time, datetime) else BASE_TIME + timedelta(minutes=index)
    )
    ingested = (
        ingestion_time
        if isinstance(ingestion_time, datetime)
        else moment + timedelta(minutes=offline_duration_minutes)
    )
    return Transaction(
        transaction_id=transaction_id or f"txn_{index:07d}",
        account_id=account_id or f"acct_{index % 7:04d}",
        device_id=device_id,
        merchant_id=merchant_id,
        amount=amount,
        currency="USD",
        event_time=event_time if isinstance(event_time, str) else iso(moment),
        ingestion_time=ingestion_time if isinstance(ingestion_time, str) else iso(ingested),
        offline_duration_minutes=offline_duration_minutes,
        signature_valid=signature_valid,
        event_id=event_id or f"evt_{index:07d}",
        label=label,
        scenario=scenario,
        **extra,
    )


def make_event(index: int = 0, *, signature_valid: bool = True, **extra: Any) -> SyncEvent:
    """Build a sync event that matches ``make_transaction`` defaults."""
    transaction = make_transaction(index, signature_valid=signature_valid, **extra)
    return SyncEvent(
        event_id=transaction.event_id,
        transaction_id=transaction.transaction_id,
        event_time=transaction.event_time,
        ingestion_time=transaction.ingestion_time,
        source="test-device",
        sequence=index,
        signature_valid=signature_valid,
    )


@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Path]]:
    """Point the pipeline at a temporary data directory.

    The pipeline imports its file constants by name, so they must be patched on
    the pipeline module rather than on ``meshshield.config`` alone.
    """
    from meshshield.core import pipeline

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    paths = {
        "data": data_dir,
        "transactions": data_dir / "transactions.jsonl",
        "events": data_dir / "sync_events.jsonl",
        "model": data_dir / "model.json",
        "baseline_model": data_dir / "baseline_model.json",
        "metrics": data_dir / "metrics.json",
        "calibration": data_dir / "calibration.json",
        "card": data_dir / "dataset_card.json",
    }
    monkeypatch.setattr(pipeline, "DATA_DIR", data_dir)
    monkeypatch.setattr(pipeline, "TRANSACTIONS_FILE", paths["transactions"])
    monkeypatch.setattr(pipeline, "EVENTS_FILE", paths["events"])
    monkeypatch.setattr(pipeline, "MODEL_FILE", paths["model"])
    monkeypatch.setattr(pipeline, "METRICS_FILE", paths["metrics"])
    monkeypatch.setattr(pipeline, "CALIBRATION_FILE", paths["calibration"])
    yield paths


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
