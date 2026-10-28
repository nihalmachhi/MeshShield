from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from meshshield.core.domain import SyncEvent
from meshshield.data.storage import IdempotencyStore


def event(event_id: str, transaction_id: str, sequence: int) -> SyncEvent:
    stamp = "2025-01-01T00:00:00Z"
    return SyncEvent(event_id, transaction_id, stamp, stamp, "test", sequence, True)


def test_sqlite_idempotency_is_safe_for_concurrent_requests(tmp_path: Path):
    store = IdempotencyStore(tmp_path / "events.sqlite3")
    try:
        with ThreadPoolExecutor(max_workers=12) as pool:
            accepted = list(pool.map(lambda _: store.accept(event("same", "tx", 1)), range(24)))
        assert sum(accepted) == 1
    finally:
        store.close()
