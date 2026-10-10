"""Core data contracts. All timestamps are UTC ISO-8601 strings."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


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

    def validate(self) -> None:
        if not self.transaction_id or not self.event_id:
            raise ValueError("transaction_id and event_id are required")
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if self.offline_duration_minutes < 0:
            raise ValueError("offline duration cannot be negative")
        if self.label not in (None, 0, 1):
            raise ValueError("label must be 0, 1, or null")
        datetime.fromisoformat(self.event_time.replace("Z", "+00:00"))
        datetime.fromisoformat(self.ingestion_time.replace("Z", "+00:00"))

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
