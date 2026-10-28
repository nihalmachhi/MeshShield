"""Streaming adapters for supported public fraud research datasets."""

import csv
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

from meshshield.core.domain import Transaction


def load_paysim(path: Path, limit: int | None = None) -> Iterator[Transaction]:
    """Read PaySim CSV rows as events; PaySim is synthetic mobile-money data."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"step", "type", "amount", "nameOrig", "nameDest", "isFraud"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"PaySim CSV missing required columns: {sorted(required)}")
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break
            event_at = datetime(2020, 1, 1, tzinfo=UTC) + timedelta(hours=int(row["step"]))
            identifier = str(row["step"]) + "-" + str(index)
            tx = Transaction(
                transaction_id=f"paysim-{identifier}",
                account_id=row["nameOrig"],
                device_id=row["nameOrig"],
                merchant_id=row["nameDest"],
                amount=float(row["amount"]),
                currency="UNKNOWN",
                event_time=event_at.isoformat(),
                ingestion_time=event_at.isoformat(),
                offline_duration_minutes=0,
                signature_valid=True,
                event_id=f"paysim-event-{identifier}",
                label=int(row["isFraud"]),
                scenario="public_dataset",
            )
            tx.validate()
            yield tx


def load_ieee_cis(
    transaction_path: Path, identity_path: Path | None = None, limit: int | None = None
) -> Iterator[Transaction]:
    """Read IEEE-CIS training transactions with an optional identity join."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer")
    identities: dict[str, dict[str, str]] = {}
    if identity_path is not None:
        with identity_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if "TransactionID" not in (reader.fieldnames or ()):
                raise ValueError("IEEE-CIS identity CSV must contain TransactionID")
            for row in reader:
                identities[str(row["TransactionID"])] = row
    with transaction_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"TransactionID", "TransactionDT", "TransactionAmt", "ProductCD", "isFraud"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"IEEE-CIS training CSV missing required columns: {sorted(required)}")
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break
            identifier = str(row["TransactionID"])
            identity = identities.get(identifier, {})
            seconds = int(float(row["TransactionDT"]))
            event_at = datetime(2017, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)
            card_id = row.get("card1") or f"unknown-card-{identifier}"
            device_id = identity.get("DeviceInfo") or identity.get("DeviceType") or "unknown-device"
            tx = Transaction(
                transaction_id=f"ieee-cis-{identifier}",
                account_id=f"card-{card_id}",
                device_id=device_id,
                merchant_id=f"product-{row['ProductCD']}",
                amount=float(row["TransactionAmt"]),
                currency="UNKNOWN",
                event_time=event_at.isoformat(),
                ingestion_time=event_at.isoformat(),
                offline_duration_minutes=0,
                signature_valid=True,
                event_id=f"ieee-cis-event-{identifier}",
                label=int(row["isFraud"]),
                scenario="public_dataset",
            )
            tx.validate()
            yield tx
