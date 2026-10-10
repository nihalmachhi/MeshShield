"""Paths and defaults shared by the application."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "generated"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TRANSACTIONS_FILE = DATA_DIR / "transactions.jsonl"
EVENTS_FILE = DATA_DIR / "sync_events.jsonl"
MODEL_FILE = DATA_DIR / "model.json"
METRICS_FILE = DATA_DIR / "metrics.json"
DATABASE_FILE = DATA_DIR / "meshshield.sqlite3"
DEFAULT_SEED = 2025
DEFAULT_TRANSACTION_COUNT = 1600
FEATURES = (
    "log_amount",
    "hour_sin",
    "hour_cos",
    "account_velocity_1h",
    "device_accounts_seen",
    "merchant_velocity_1h",
    "offline_duration_minutes",
    "is_delayed_sync",
    "account_transaction_count",
)
GRAPH_FEATURES = FEATURES + (
    "account_device_degree",
    "device_recent_accounts_24h",
)
