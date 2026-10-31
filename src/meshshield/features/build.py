"""Point-in-time feature construction. Histories only include earlier event times."""

import math
from collections import defaultdict, deque
from datetime import datetime, timedelta
from itertools import groupby

from meshshield.config import FEATURES, GRAPH_FEATURES
from meshshield.core.domain import Transaction, parse_timestamp


class _DisjointSets:
    """Union-find over account and device nodes, updated edge by edge."""

    def __init__(self) -> None:
        self._parent: dict[str, str] = {}
        self._size: dict[str, int] = {}

    def add(self, node: str) -> None:
        if node not in self._parent:
            self._parent[node] = node
            self._size[node] = 1

    def find(self, node: str) -> str:
        root = node
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[node] != root:
            self._parent[node], node = root, self._parent[node]
        return root

    def union(self, left: str, right: str) -> None:
        self.add(left)
        self.add(right)
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self._size[left_root] < self._size[right_root]:
            left_root, right_root = right_root, left_root
        self._parent[right_root] = left_root
        self._size[left_root] += self._size[right_root]

    def component_size(self, node: str) -> float:
        """Size of the node's component, or 0 when the node has no history yet."""
        if node not in self._parent:
            return 0.0
        return float(self._size[self.find(node)])


def _time(value: str) -> datetime:
    return parse_timestamp(value)


def build_features(transactions: list[Transaction]) -> dict[str, dict[str, float]]:
    ordered = sorted(transactions, key=lambda tx: (_time(tx.event_time), tx.transaction_id))
    account_history: dict[str, deque[datetime]] = defaultdict(deque)
    merchant_history: dict[str, deque[datetime]] = defaultdict(deque)
    device_accounts: dict[str, set[str]] = defaultdict(set)
    account_devices: dict[str, set[str]] = defaultdict(set)
    merchant_devices: dict[str, set[str]] = defaultdict(set)
    account_merchants: dict[str, set[str]] = defaultdict(set)
    device_history: dict[str, deque[tuple[datetime, str]]] = defaultdict(deque)
    account_count: dict[str, int] = defaultdict(int)
    device_count: dict[str, int] = defaultdict(int)
    components = _DisjointSets()
    result: dict[str, dict[str, float]] = {}
    for moment, group in groupby(ordered, key=lambda tx: _time(tx.event_time)):
        same_time_transactions = list(group)
        one_hour_ago = moment - timedelta(hours=1)
        day_ago = moment - timedelta(hours=24)
        hour = moment.hour + moment.minute / 60
        for tx in same_time_transactions:
            account_events = account_history[tx.account_id]
            merchant_events = merchant_history[tx.merchant_id]
            device_events = device_history[tx.device_id]
            while account_events and account_events[0] < one_hour_ago:
                account_events.popleft()
            while merchant_events and merchant_events[0] < one_hour_ago:
                merchant_events.popleft()
            while device_events and device_events[0][0] < day_ago:
                device_events.popleft()
            reachable: set[str] = set()
            for device in account_devices[tx.account_id]:
                reachable |= device_accounts[device]
            reachable.discard(tx.account_id)
            result[tx.transaction_id] = {
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
                "device_transaction_count": float(device_count[tx.device_id]),
                "merchant_device_degree": float(len(merchant_devices[tx.merchant_id])),
                "account_merchant_degree": float(len(account_merchants[tx.account_id])),
                "two_hop_account_reach": float(len(reachable)),
                "account_component_size": components.component_size(f"account:{tx.account_id}"),
                "device_component_size": components.component_size(f"device:{tx.device_id}"),
            }
        # Events sharing a timestamp become visible only after every peer's row.
        for tx in same_time_transactions:
            account_history[tx.account_id].append(moment)
            merchant_history[tx.merchant_id].append(moment)
            device_history[tx.device_id].append((moment, tx.account_id))
            device_accounts[tx.device_id].add(tx.account_id)
            account_devices[tx.account_id].add(tx.device_id)
            merchant_devices[tx.merchant_id].add(tx.device_id)
            account_merchants[tx.account_id].add(tx.merchant_id)
            account_count[tx.account_id] += 1
            device_count[tx.device_id] += 1
            components.union(f"account:{tx.account_id}", f"device:{tx.device_id}")
    return result


def vector(row: dict[str, float], graph: bool = True) -> list[float]:
    names = GRAPH_FEATURES if graph else FEATURES
    return [float(row.get(name, 0.0)) for name in names]
