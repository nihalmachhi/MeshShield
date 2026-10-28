import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from meshshield.domain import SyncEvent, Transaction, parse_timestamp
from meshshield.evaluation import evaluate
from meshshield.features import build_features
from meshshield.model import LogisticModel, feature_names
from meshshield.rules import inspect_event_order
from meshshield.storage import IdempotencyStore


def transaction(transaction_id: str, event_id: str, event_time: str,
                account_id: str = "account") -> Transaction:
    return Transaction(transaction_id, account_id, "device", "merchant", 12.0, "INR",
                       event_time, event_time, 0, True, event_id, 0)


def event(event_id: str, transaction_id: str, sequence: int) -> SyncEvent:
    stamp = "2025-01-01T00:00:00Z"
    return SyncEvent(event_id, transaction_id, stamp, stamp, "test", sequence, True)


def test_timestamp_requires_timezone_and_normalizes_to_utc():
    assert parse_timestamp("2025-01-01T01:00:00+01:00") == parse_timestamp("2025-01-01T00:00:00Z")
    with pytest.raises(ValueError):
        parse_timestamp("2025-01-01T00:00:00")


def test_features_do_not_use_future_or_same_time_peer_data():
    first = transaction("a", "e1", "2025-01-01T00:00:00Z")
    future = transaction("b", "e2", "2025-01-01T00:01:00Z")
    same_time_peer = transaction("c", "e3", "2025-01-01T00:00:00Z")
    baseline = build_features([first])["a"]
    expanded = build_features([future, same_time_peer, first])
    assert expanded["a"] == baseline
    assert expanded["c"]["account_velocity_1h"] == 0


def test_sqlite_idempotency_is_safe_for_concurrent_requests(tmp_path: Path):
    store = IdempotencyStore(tmp_path / "events.sqlite3")
    try:
        with ThreadPoolExecutor(max_workers=12) as pool:
            accepted = list(pool.map(lambda _: store.accept(event("same", "tx", 1)), range(24)))
        assert sum(accepted) == 1
    finally:
        store.close()


def test_evaluation_handles_zero_positives_and_rejects_mismatched_input():
    assert evaluate([0, 0], [0.1, 0.8])["pr_auc_average_precision"] == 0
    with pytest.raises(ValueError, match="same length"):
        evaluate([1], [])


def test_sync_order_checks_parsed_timestamps():
    regressed = SyncEvent("e2", "b", "2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z",
                          "test", 2, True)
    earlier = SyncEvent("e1", "a", "2024-12-31T19:00:00-05:00", "2025-01-01T00:00:00Z",
                        "test", 1, True)
    assert "event_time_regressed_with_sequence" not in inspect_event_order([earlier, regressed])


def test_model_uses_class_weights_and_converges():
    model = LogisticModel.fit([[0.0], [1.0], [2.0], [3.0]], [0, 0, 0, 1], ("x",), epochs=1000)
    assert model.score([3.0]) > model.score([0.0])


def test_web_rejects_bad_limit_and_surfaces_replay(monkeypatch, tmp_path: Path):
    from meshshield import web

    stamp = "2025-01-01T00:00:00Z"
    transactions = [transaction("first", "reused-event", stamp),
                    transaction("second", "reused-event", "2025-01-01T00:01:00Z")]
    model = LogisticModel(feature_names(True), [0.0] * len(feature_names(True)),
                          [1.0] * len(feature_names(True)), [0.0] * len(feature_names(True)), 0.0)
    events = [event("reused-event", "first", 0),
              SyncEvent("reused-event", "second", "2025-01-01T00:01:00Z",
                        "2025-01-01T00:01:00Z", "test", 1, True)]
    event_file = tmp_path / "events.jsonl"
    event_file.write_text("\n".join(json.dumps(item.to_dict()) for item in events), encoding="utf-8")
    monkeypatch.setattr(web, "load_or_prepare", lambda: (transactions, {}, model))
    monkeypatch.setattr(web, "EVENTS_FILE", event_file)
    monkeypatch.setattr(web, "DATABASE_FILE", tmp_path / "db.sqlite3")
    handler_type = web.create_handler()

    def request(path: str):
        handler = handler_type.__new__(handler_type)
        handler.path = path
        captured = []
        handler._json = lambda payload, status=200: captured.append((payload, status))
        handler.do_GET()
        return captured[-1]

    payload, status = request("/api/transactions?limit=abc")
    assert status == 400
    assert "integer" in payload["error"]
    payload, status = request("/api/transactions?limit=2")
    assert status == 200
    assert "replayed_event_id" in payload[1]["integrity_findings"]
    payload, status = request("/api/health")
    assert status == 200 and payload["status"] == "ok"
    monkeypatch.setattr(web, "score_transaction", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError()))
    payload, status = request("/api/transactions?limit=1")
    assert status == 500 and payload["error"] == "internal server error"

