from meshshield.core.domain import Transaction
from meshshield.features.build import build_features


def transaction(
    transaction_id: str, event_id: str, event_time: str, account_id: str = "account"
) -> Transaction:
    return Transaction(
        transaction_id,
        account_id,
        "device",
        "merchant",
        12.0,
        "INR",
        event_time,
        event_time,
        0,
        True,
        event_id,
        0,
    )


def test_features_do_not_use_future_or_same_time_peer_data():
    first = transaction("a", "e1", "2025-01-01T00:00:00Z")
    future = transaction("b", "e2", "2025-01-01T00:01:00Z")
    same_time_peer = transaction("c", "e3", "2025-01-01T00:00:00Z")
    baseline = build_features([first])["a"]
    expanded = build_features([future, same_time_peer, first])
    assert expanded["a"] == baseline
    assert expanded["c"]["account_velocity_1h"] == 0
