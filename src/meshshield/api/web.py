"""Minimal local review UI and JSON API using only Python's standard library."""

import json
import logging
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from meshshield.config import DATABASE_FILE, EVENTS_FILE, SITE_DIR
from meshshield.core.domain import SyncEvent
from meshshield.core.pipeline import load_or_prepare, score_transaction
from meshshield.data.storage import IdempotencyStore, read_jsonl
from meshshield.features.build import build_features
from meshshield.sync.simulator import process_delivery, simulate_delivery

logger = logging.getLogger(__name__)


def create_handler() -> type[BaseHTTPRequestHandler]:
    transactions, metrics, model, calibrator, threshold = load_or_prepare()
    by_id = {tx.transaction_id: tx for tx in transactions}
    arrival_index = {tx.transaction_id: index for index, tx in enumerate(transactions)}
    feature_rows = build_features(transactions)
    events = [SyncEvent(**row) for row in read_jsonl(EVENTS_FILE)]
    store = IdempotencyStore(DATABASE_FILE)
    delivery_store = IdempotencyStore(":memory:")
    delivery_summary = process_delivery(simulate_delivery(events), delivery_store)
    delivery_store.close()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, value: Any, status: int = 200) -> None:
            self._send(json.dumps(value).encode("utf-8"), "application/json; charset=utf-8", status)

        def do_GET(self) -> None:
            try:
                self._handle_get()
            except Exception as exc:
                logger.exception("GET request failed: %s", type(exc).__name__)
                self._json({"error": "internal server error"}, 500)

        def _handle_get(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/health":
                self._json({"status": "ok", "synthetic_only": True})
            elif path == "/api/metrics":
                self._json({"metrics": metrics, "sync_simulation": delivery_summary})
            elif path == "/api/transactions":
                query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
                limit = 100
                if "limit" in query:
                    raw_limit = query["limit"]
                    if len(raw_limit) != 1 or not raw_limit[0].isdigit():
                        self._json({"error": "limit must be an integer between 1 and 500"}, 400)
                        return
                    limit = int(raw_limit[0])
                    if not 1 <= limit <= 500:
                        self._json({"error": "limit must be an integer between 1 and 500"}, 400)
                        return
                scored = []
                seen_tx: set[str] = set()
                seen_events: set[str] = set()
                for tx in transactions[:limit]:
                    item = score_transaction(
                        tx, [], model, feature_rows, seen_tx, seen_events, calibrator, threshold
                    )
                    item.update(
                        {
                            "amount": tx.amount,
                            "account_id": tx.account_id,
                            "device_id": tx.device_id,
                            "merchant_id": tx.merchant_id,
                            "event_time": tx.event_time,
                            "label": tx.label,
                            "scenario": tx.scenario,
                        }
                    )
                    scored.append(item)
                    seen_tx.add(tx.transaction_id)
                    seen_events.add(tx.event_id)
                self._json(scored)
            elif path.startswith("/api/transactions/"):
                transaction_id = path.rsplit("/", 1)[-1]
                found_tx = by_id.get(transaction_id)
                if found_tx is None:
                    self._json({"error": "transaction not found"}, 404)
                else:
                    prior = transactions[: arrival_index[transaction_id]]
                    self._json(
                        score_transaction(
                            found_tx,
                            prior,
                            model,
                            feature_rows,
                            {item.transaction_id for item in prior},
                            {item.event_id for item in prior},
                            calibrator,
                            threshold,
                        )
                    )
            elif path.startswith("/api/"):
                self._json({"error": "not found"}, 404)
            else:
                requested = unquote(path).lstrip("/") or "index.html"
                target = (SITE_DIR / requested).resolve()
                if not target.is_relative_to(SITE_DIR.resolve()):
                    self._json({"error": "not found"}, 404)
                    return
                if not target.is_file() and "." not in Path(requested).name:
                    target = SITE_DIR / "index.html"
                if not target.is_file():
                    self._json(
                        {"error": "React site is not built; run npm --prefix site run build"}, 503
                    )
                    return
                content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                if content_type.startswith("text/") or content_type in {
                    "application/javascript",
                    "application/json",
                }:
                    content_type += "; charset=utf-8"
                self._send(target.read_bytes(), content_type)

        def do_POST(self) -> None:
            try:
                self._handle_post()
            except Exception as exc:
                logger.exception("POST request failed: %s", type(exc).__name__)
                self._json({"error": "internal server error"}, 500)

        def _handle_post(self) -> None:
            if urlparse(self.path).path != "/api/replay":
                self._json({"error": "not found"}, 404)
                return
            original = next(event for event in events if event.signature_valid)
            # Re-deliver the same identifier; SQLite rejects the second arrival.
            event = SyncEvent(
                original.event_id,
                original.transaction_id,
                original.event_time,
                original.ingestion_time,
                original.source,
                original.sequence,
                original.signature_valid,
            )
            first = store.accept(event)
            second = store.accept(event)
            self._json(
                {
                    "event_id": event.event_id,
                    "first_delivery_accepted": first,
                    "retry_accepted": second,
                    "idempotency_working": first and not second,
                }
            )

        def log_message(self, format: str, *args: object) -> None:
            message = format % args if args else format
            logger.info("%s %s", self.log_date_time_string(), message)

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), create_handler())
    print(f"MeshShield review UI: http://{host}:{port} (synthetic research data only)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping MeshShield.")
    finally:
        server.server_close()
