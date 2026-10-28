"""Deterministic integrity checks separate from the probabilistic model."""

from itertools import pairwise

from meshshield.core.domain import SyncEvent, Transaction, parse_timestamp


def inspect_transaction(
    tx: Transaction,
    seen_transaction_ids: set[str] | None = None,
    seen_event_ids: set[str] | None = None,
) -> list[str]:
    seen_transaction_ids = seen_transaction_ids if seen_transaction_ids is not None else set()
    seen_event_ids = seen_event_ids if seen_event_ids is not None else set()
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
    if any(value < 0 for value in sequences):
        findings.append("negative_sequence")
    if any(
        parse_timestamp(event.ingestion_time) < parse_timestamp(event.event_time)
        for event in events
    ):
        findings.append("ingestion_before_event_time")
    by_sequence = sorted(events, key=lambda event: event.sequence)
    if any(
        parse_timestamp(left.event_time) > parse_timestamp(right.event_time)
        for left, right in pairwise(by_sequence)
    ):
        findings.append("event_time_regressed_with_sequence")
    return findings
