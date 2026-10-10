"""Small persistence adapters: JSON Lines for datasets and SQLite for idempotency."""

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator

from meshshield.domain import SyncEvent, Transaction


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on {path}:{line_number}") from exc


class IdempotencyStore:
    """Persist accepted IDs so a retried sync event cannot be applied twice."""

    def __init__(self, path: Path | str):
        path = str(path)
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, accepted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        self.connection.commit()

    def accept(self, event: SyncEvent) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO processed_events(event_id, transaction_id) VALUES (?, ?)",
            (event.event_id, event.transaction_id),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def close(self) -> None:
        self.connection.close()


def load_transactions(path: Path) -> list[Transaction]:
    return [Transaction.from_dict(row) for row in read_jsonl(path)]
