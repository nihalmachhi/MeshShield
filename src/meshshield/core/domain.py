"""Core data contracts. All timestamps are UTC ISO-8601 strings."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


def parse_timestamp(value: str) -> datetime:
    """Parse ISO-8601 timestamps and normalize them to UTC for ordering."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    account_id: str
    device_id: str
    merchant_id: str
    amount: float
    currency: str
    event_time: str
    ingestion_time: str
    offline_duration_minutes: int
    signature_valid: bool
    event_id: str
    label: int | None = None
    scenario: str = "normal"
    device_counter: int = 0
    key_id: str = ""
    signature: str = ""
    clock_offset_seconds: float = 0.0

    def validate(self) -> None:
        if not self.transaction_id or not self.event_id:
            raise ValueError("transaction_id and event_id are required")
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if self.offline_duration_minutes < 0:
            raise ValueError("offline duration cannot be negative")
        if self.device_counter < 0:
            raise ValueError("device counter cannot be negative")
        if self.label not in (None, 0, 1):
            raise ValueError("label must be 0, 1, or null")
        event_time = parse_timestamp(self.event_time)
        ingestion_time = parse_timestamp(self.ingestion_time)
        # Device clocks are allowed to be slightly ahead: the integrity gate
        # flags `event_time_in_future`, it does not silently rewrite the event.
        if (event_time - ingestion_time) > timedelta(minutes=15):
            raise ValueError("event_time is implausibly far ahead of ingestion_time")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Transaction":
        transaction = cls(**value)
        transaction.validate()
        return transaction


@dataclass(frozen=True)
class SyncEvent:
    event_id: str
    transaction_id: str
    event_time: str
    ingestion_time: str
    source: str
    sequence: int
    signature_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
