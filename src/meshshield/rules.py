"""Deterministic integrity checks separate from the probabilistic model."""

from meshshield.domain import SyncEvent, Transaction


def inspect_transaction(tx: Transaction, seen_transaction_ids: set[str] | None = None,
                        seen_event_ids: set[str] | None = None) -> list[str]:
    seen_transaction_ids = seen_transaction_ids or set()
    seen_event_ids = seen_event_ids or set()
    findings: list[str] = []
    if tx.transaction_id in seen_transaction_ids:
        findings.append("duplicate_transaction_id")
    if tx.event_id in seen_event_ids:
        findings.append("replayed_event_id")
    if not tx.signature_valid:
        findings.append("invalid_simulated_signature")
    if tx.amount <= 0 or tx.offline_duration_minutes < 0:
        findings.append("invalid_transaction_fields")
    return findings


def inspect_event_order(events: list[SyncEvent]) -> list[str]:
    findings: list[str] = []
    sequences = [event.sequence for event in events]
    if len(sequences) != len(set(sequences)):
        findings.append("duplicate_sequence")
    event_times = [event.event_time for event in events]
    ingestion_times = [event.ingestion_time for event in events]
    if any(value < 0 for value in sequences):
        findings.append("negative_sequence")
    if len(event_times) != len(ingestion_times):
        findings.append("inconsistent_sync_history")
    by_sequence = sorted(events, key=lambda event: event.sequence)
    if any(left.event_time > right.event_time
           for left, right in zip(by_sequence, by_sequence[1:])):
        findings.append("event_time_regressed_with_sequence")
    return findings
