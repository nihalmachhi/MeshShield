"""Delayed, duplicate, and out-of-order offline queue simulation."""

from typing import Protocol

from meshshield.core.domain import SyncEvent, Transaction, parse_timestamp


class EventStore(Protocol):
    def accept(self, event: SyncEvent) -> bool: ...


def simulate_delivery(events: list[SyncEvent], duplicate_every: int = 17) -> list[SyncEvent]:
    delivered: list[SyncEvent] = []
    for index, event in enumerate(events):
        delivered.append(event)
        if duplicate_every and index % duplicate_every == 0:
            delivered.append(event)
    # A small deterministic swap models a delayed/out-of-order network delivery.
    for index in range(0, len(delivered) - 1, 23):
        delivered[index], delivered[index + 1] = delivered[index + 1], delivered[index]
    return delivered


def flag_late_arrivals(
    transactions: list[Transaction], threshold_minutes: int = 120
) -> dict[str, int]:
    """Return transaction IDs whose sync delay exceeds ``threshold_minutes``.

    A late arrival is a delivery fact, not a feature change: callers may report it
    for review, but historical feature rows must stay identical.
    """
    late: dict[str, int] = {}
    for tx in transactions:
        arrival = parse_timestamp(tx.ingestion_time)
        event = parse_timestamp(tx.event_time)
        delay_minutes = int((arrival - event).total_seconds() // 60)
        if delay_minutes > threshold_minutes:
            late[tx.transaction_id] = delay_minutes
    return late


def process_delivery(events: list[SyncEvent], store: EventStore) -> dict[str, int]:
    accepted = duplicates = invalid = 0
    for event in events:
        if not event.signature_valid:
            invalid += 1
        elif store.accept(event):
            accepted += 1
        else:
            duplicates += 1
    return {
        "delivered": len(events),
        "accepted": accepted,
        "duplicate_deliveries_ignored": duplicates,
        "invalid_signatures_rejected": invalid,
    }
