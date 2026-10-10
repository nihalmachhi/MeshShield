"""Point-in-time feature construction. Histories only include earlier event times."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
import math

from meshshield.config import FEATURES, GRAPH_FEATURES
from meshshield.domain import Transaction


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_features(transactions: list[Transaction]) -> dict[str, dict[str, float]]:
    ordered = sorted(transactions, key=lambda tx: (_time(tx.event_time), tx.transaction_id))
    account_history: dict[str, deque[datetime]] = defaultdict(deque)
    merchant_history: dict[str, deque[datetime]] = defaultdict(deque)
    device_accounts: dict[str, set[str]] = defaultdict(set)
    account_devices: dict[str, set[str]] = defaultdict(set)
    device_history: dict[str, deque[tuple[datetime, str]]] = defaultdict(deque)
    account_count: dict[str, int] = defaultdict(int)
    result: dict[str, dict[str, float]] = {}
    for tx in ordered:
        moment = _time(tx.event_time)
        one_hour_ago = moment - timedelta(hours=1)
        day_ago = moment - timedelta(hours=24)
        account_events = account_history[tx.account_id]
        merchant_events = merchant_history[tx.merchant_id]
        device_events = device_history[tx.device_id]
        while account_events and account_events[0] < one_hour_ago:
            account_events.popleft()
        while merchant_events and merchant_events[0] < one_hour_ago:
            merchant_events.popleft()
        while device_events and device_events[0][0] < day_ago:
            device_events.popleft()
        hour = moment.hour + moment.minute / 60
        base = {
            "log_amount": math.log1p(tx.amount),
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "account_velocity_1h": float(len(account_events)),
            "device_accounts_seen": float(len(device_accounts[tx.device_id])),
            "merchant_velocity_1h": float(len(merchant_events)),
            "offline_duration_minutes": float(tx.offline_duration_minutes),
            "is_delayed_sync": float(tx.offline_duration_minutes >= 30),
            "account_transaction_count": float(account_count[tx.account_id]),
            "account_device_degree": float(len(account_devices[tx.account_id])),
            "device_recent_accounts_24h": float(len({a for _, a in device_events})),
        }
        result[tx.transaction_id] = base
        # Add the current event only after its features have been recorded.
        account_events.append(moment)
        merchant_events.append(moment)
        device_events.append((moment, tx.account_id))
        device_accounts[tx.device_id].add(tx.account_id)
        account_devices[tx.account_id].add(tx.device_id)
        account_count[tx.account_id] += 1
    return result


def vector(row: dict[str, float], graph: bool = True) -> list[float]:
    names = GRAPH_FEATURES if graph else FEATURES
    return [float(row.get(name, 0.0)) for name in names]
