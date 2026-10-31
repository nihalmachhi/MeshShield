"""Exactly-once delivery: the claim the SQLite store exists to make."""

from __future__ import annotations

import threading
from pathlib import Path

from conftest import make_event

from meshshield.data.storage import IdempotencyStore


def test_the_same_event_is_accepted_exactly_once(tmp_path: Path) -> None:
    store = IdempotencyStore(tmp_path / "idempotency.sqlite3")
    event = make_event(1, signature_valid=True)
    results = [store.accept(event) for _ in range(5)]
    store.close()

    assert results == [True, False, False, False, False]
    assert results.count(True) == 1
    assert results.count(False) == 4


def test_the_accepted_set_survives_reopening_the_file(tmp_path: Path) -> None:
    path = tmp_path / "idempotency.sqlite3"
    event = make_event(2)
    with IdempotencyStore(path) as store:  # type: ignore[attr-defined]
        assert store.accept(event) is True
    reopened = IdempotencyStore(path)
    assert reopened.accept(event) is False
    reopened.close()


def test_concurrent_deliveries_still_accept_once(tmp_path: Path) -> None:
    store = IdempotencyStore(tmp_path / "concurrent.sqlite3")
    event = make_event(3)
    results: list[bool] = []
    lock = threading.Lock()
    barrier = threading.Barrier(16)

    def deliver() -> None:
        barrier.wait()
        accepted = store.accept(event)
        with lock:
            results.append(accepted)

    threads = [threading.Thread(target=deliver) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    store.close()

    assert len(results) == 16
    assert results.count(True) == 1


def test_distinct_events_are_both_accepted(tmp_path: Path) -> None:
    store = IdempotencyStore(tmp_path / "distinct.sqlite3")
    assert store.accept(make_event(10)) is True
    assert store.accept(make_event(11)) is True
    store.close()
