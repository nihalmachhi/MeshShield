"""Graph features must be causal, incremental and reproducible."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from meshshield.core.domain import Transaction
from meshshield.features.build import build_features
from meshshield.features.graph import community_labels, graph_summary, pagerank

START = datetime(2025, 1, 1, tzinfo=UTC)


def tx(
    index: int,
    account: str,
    device: str,
    *,
    minute: int | None = None,
    merchant: str = "merchant_001",
) -> Transaction:
    moment = START + timedelta(minutes=index if minute is None else minute)
    return Transaction(
        transaction_id=f"txn_{index:04d}",
        account_id=account,
        device_id=device,
        merchant_id=merchant,
        amount=20.0,
        currency="USD",
        event_time=moment.isoformat().replace("+00:00", "Z"),
        ingestion_time=(moment + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        offline_duration_minutes=5,
        signature_valid=True,
        event_id=f"evt_{index:04d}",
        label=0,
        scenario="normal",
    )


def test_a_ring_shares_one_component_but_only_after_its_events() -> None:
    first = tx(0, "acct_ring_a", "device_ring")
    second = tx(1, "acct_ring_b", "device_ring")
    third = tx(2, "acct_ring_c", "device_ring")
    features = build_features([first, second, third])
    # A device's component is account plus device after the first edge exists.
    assert features["txn_0000"]["device_component_size"] == 0.0
    assert features["txn_0001"]["device_component_size"] == 2.0
    # Third event sees the first two accounts plus the shared device.
    assert features["txn_0002"]["device_component_size"] == 3.0
    assert features["txn_0002"]["account_component_size"] == 0.0
    assert features["txn_0002"]["device_accounts_seen"] == 2.0
    # A brand-new account has no prior devices, so no two-hop reach yet.
    assert features["txn_0002"]["two_hop_account_reach"] == 0.0


def test_two_hop_reach_uses_the_accounts_earlier_devices() -> None:
    first = tx(0, "acct_a", "device_shared")
    second = tx(1, "acct_b", "device_shared")
    third = tx(2, "acct_a", "device_shared")
    features = build_features([first, second, third])
    assert features["txn_0002"]["two_hop_account_reach"] == 1.0
    assert features["txn_0002"]["account_component_size"] == 3.0


def test_future_ring_members_never_change_earlier_rows() -> None:
    past = tx(0, "acct_0001", "device_0001")
    baseline = build_features([past])["txn_0000"]
    future = [
        tx(index, f"acct_{index:04d}", "device_0001", minute=60 + index) for index in range(1, 6)
    ]
    expanded = build_features([past, *future])["txn_0000"]
    assert expanded == baseline
    assert expanded["account_component_size"] == 0.0


def test_device_and_merchant_counts_use_earlier_history() -> None:
    first = tx(0, "acct_a", "device_shared")
    second = tx(1, "acct_a", "device_shared", merchant="merchant_002")
    third = tx(2, "acct_b", "device_shared")
    features = build_features([first, second, third])
    assert features["txn_0000"]["device_transaction_count"] == 0.0
    assert features["txn_0001"]["device_transaction_count"] == 1.0
    assert features["txn_0002"]["device_transaction_count"] == 2.0
    assert features["txn_0001"]["account_merchant_degree"] == 1.0
    assert features["txn_0002"]["merchant_device_degree"] == 1.0


def test_same_timestamp_peers_are_invisible_to_each_other() -> None:
    left = tx(0, "acct_a", "device_shared", minute=0)
    right = tx(1, "acct_b", "device_shared", minute=0)
    features = build_features([left, right])
    assert features["txn_0000"]["two_hop_account_reach"] == 0.0
    assert features["txn_0001"]["two_hop_account_reach"] == 0.0
    assert features["txn_0000"]["account_component_size"] == 0.0


def test_pagerank_is_deterministic_and_normalised() -> None:
    edges = [("acct_a", "device_1"), ("acct_b", "device_1"), ("acct_b", "device_2")]
    ranks = pagerank(edges)
    assert math.isclose(sum(ranks.values()), 1.0)
    assert ranks == pagerank(list(reversed(edges)))
    assert pagerank([]) == {}


def test_community_labels_are_dense_and_stable() -> None:
    edges = [("acct_a", "device_1"), ("acct_b", "device_1"), ("acct_c", "device_2")]
    labels, backend = community_labels(edges)
    assert backend in {"networkx-greedy-modularity", "label-propagation"}
    assert set(labels) == {"acct_a", "acct_b", "acct_c", "device_1", "device_2"}
    assert sorted(set(labels.values())) == list(range(len(set(labels.values()))))


def test_graph_summary_reports_snapshot_statistics() -> None:
    transactions = [
        tx(0, "acct_a", "device_1"),
        tx(1, "acct_b", "device_1"),
        tx(2, "acct_c", "device_2"),
    ]
    summary = graph_summary(transactions, top_n=3)
    assert summary["edge_count"] == 3
    assert summary["node_count"] == 5
    assert len(summary["pagerank_top"]) == 3
    assert "not used as training features" in str(summary["note"])
