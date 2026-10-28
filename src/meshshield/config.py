"""Paths and defaults shared by the application."""

import os
from pathlib import Path


def _project_root() -> Path:
    configured_root = os.getenv("MESHSHIELD_HOME")
    if configured_root:
        return Path(configured_root).expanduser().resolve()
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "site").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _project_root()
DATA_DIR = PROJECT_ROOT / "data" / "generated"
SITE_DIR = PROJECT_ROOT / "site" / "dist"
TRANSACTIONS_FILE = DATA_DIR / "transactions.jsonl"
EVENTS_FILE = DATA_DIR / "sync_events.jsonl"
MODEL_FILE = DATA_DIR / "model.json"
METRICS_FILE = DATA_DIR / "metrics.json"
CALIBRATION_FILE = DATA_DIR / "calibration.json"
DATABASE_FILE = DATA_DIR / "meshshield.sqlite3"
DEFAULT_SEED = 2025
DEFAULT_TRANSACTION_COUNT = 1600
FALSE_POSITIVE_COST = 1.0
FALSE_NEGATIVE_COST = 5.0
REVIEW_CAPACITY = 0.10
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
