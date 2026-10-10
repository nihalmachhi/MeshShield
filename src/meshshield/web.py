"""Minimal local review UI and JSON API using only Python's standard library."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import uuid
from urllib.parse import urlparse

from meshshield.config import DATABASE_FILE, FRONTEND_DIR
from meshshield.domain import SyncEvent, Transaction
from meshshield.pipeline import load_or_prepare, score_transaction
from meshshield.simulator import process_delivery, simulate_delivery
from meshshield.storage import IdempotencyStore


def create_handler():
    transactions, metrics, model = load_or_prepare()
    by_id = {tx.transaction_id: tx for tx in transactions}
    events = [SyncEvent(**row) for row in (json.loads(line) for line in
              (Path(__file__).resolve().parents[2] / "data/generated/sync_events.jsonl").read_text(encoding="utf-8").splitlines())]
    store = IdempotencyStore(DATABASE_FILE)
    delivery_store = IdempotencyStore(":memory:")
    delivery_summary = process_delivery(simulate_delivery(events), delivery_store)
    delivery_store.close()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, value, status: int = 200):
            self._send(json.dumps(value).encode("utf-8"), "application/json; charset=utf-8", status)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self._send((FRONTEND_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/health":
                self._json({"status": "ok", "synthetic_only": True})
            elif path == "/api/metrics":
                self._json({"metrics": metrics, "sync_simulation": delivery_summary})
            elif path == "/api/transactions":
                query = urlparse(self.path).query
                limit = 100
                for part in query.split("&"):
                    if part.startswith("limit="):
                        limit = max(1, min(500, int(part[6:])))
                scored = []
                for tx in transactions[:limit]:
                    # Feature construction is point-in-time; pass the full historical set
                    # so only events earlier than this transaction enter its feature row.
                    prior = [other for other in transactions
                             if other.transaction_id != tx.transaction_id
                             and other.event_time < tx.event_time]
                    item = score_transaction(tx, prior, model)
                    item.update({"amount": tx.amount, "account_id": tx.account_id,
                                 "device_id": tx.device_id, "merchant_id": tx.merchant_id,
                                 "event_time": tx.event_time, "label": tx.label,
                                 "scenario": tx.scenario})
                    scored.append(item)
                self._json(scored)
            elif path.startswith("/api/transactions/"):
                transaction_id = path.rsplit("/", 1)[-1]
                tx = by_id.get(transaction_id)
                if tx is None:
                    self._json({"error": "transaction not found"}, 404)
                else:
                    prior = [other for other in transactions
                             if other.transaction_id != tx.transaction_id
                             and other.event_time < tx.event_time]
                    self._json(score_transaction(tx, prior, model))
            else:
                self._json({"error": "not found"}, 404)

        def do_POST(self):
            if urlparse(self.path).path != "/api/replay":
                self._json({"error": "not found"}, 404)
                return
            original = next(event for event in events if event.signature_valid)
            # Give each button click a fresh local demo event while keeping the
            # repeated delivery within this request exactly idempotent.
            event = SyncEvent(f"replay_demo_{uuid.uuid4().hex}", original.transaction_id,
                              original.event_time, original.ingestion_time,
                              original.source, original.sequence, True)
            first = store.accept(event)
            second = store.accept(event)
            self._json({"event_id": event.event_id, "first_delivery_accepted": first,
                        "retry_accepted": second, "idempotency_working": first and not second})

        def log_message(self, format, *args):
            print(f"{self.log_date_time_string()} {args[0] % args[1:]}")

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8000):
    server = ThreadingHTTPServer((host, port), create_handler())
    print(f"MeshShield review UI: http://{host}:{port} (synthetic research data only)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping MeshShield.")
    finally:
        server.server_close()
