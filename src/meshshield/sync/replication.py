"""A grow-only set merge for immutable signed events with conflict quarantine."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MergeResult:
    events: tuple[dict[str, Any], ...]
    conflicting_event_ids: tuple[str, ...]


def _canonical(event: dict[str, Any]) -> str:
    return json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def merge_event_sets(*replicas: list[dict[str, Any]]) -> MergeResult:
    """Union event sets; same-ID payload conflicts are returned for quarantine."""
    payloads: dict[str, set[str]] = {}
    for replica in replicas:
        for event in replica:
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                raise ValueError("replicated events require a non-empty event_id")
            payloads.setdefault(event_id, set()).add(_canonical(event))
    conflicts = tuple(
        sorted(event_id for event_id, versions in payloads.items() if len(versions) > 1)
    )
    # A stable representative keeps the merge associative and commutative;
    # conflicts stay quarantined.
    merged = tuple(json.loads(min(versions)) for _, versions in sorted(payloads.items()))
    return MergeResult(events=merged, conflicting_event_ids=conflicts)


def payload_digest(event: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(event).encode("utf-8")).hexdigest()
