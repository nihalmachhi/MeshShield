import json
from pathlib import Path

from meshshield.api import web
from meshshield.core.domain import SyncEvent, Transaction
from meshshield.models.logistic import LogisticModel, feature_names


def transaction(transaction_id: str, event_id: str, event_time: str,
                account_id: str = "account") -> Transaction:
    return Transaction(transaction_id, account_id, "device", "merchant", 12.0, "INR",
                       event_time, event_time, 0, True, event_id, 0)

def event(event_id: str, transaction_id: str, sequence: int) -> SyncEvent:
    stamp = "2025-01-01T00:00:00Z"
    return SyncEvent(event_id, transaction_id, stamp, stamp, "test", sequence, True)

def test_web_rejects_bad_limit_and_surfaces_replay(monkeypatch, tmp_path: Path):
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
