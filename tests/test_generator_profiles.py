"""The hard profile must actually be harder, and every scenario must be reachable."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest

from meshshield.data.generator import HARD_SCENARIOS, generate

ORIGIN = datetime(2025, 1, 1, tzinfo=UTC)


def test_easy_profile_keeps_the_original_scenarios() -> None:
    transactions, _ = generate(400, seed=2, profile="easy")
    scenarios = {tx.scenario for tx in transactions}
    assert scenarios <= {
        "normal",
        "high_amount",
        "shared_device",
        "replay_attempt",
        "invalid_signature",
    }
    assert "fraud_ring" not in scenarios


@pytest.mark.parametrize("scenario", HARD_SCENARIOS)
def test_hard_profile_reaches_every_scenario(scenario: str) -> None:
    transactions, _ = generate(1200, seed=3, profile="hard")
    assert scenario in {tx.scenario for tx in transactions}


def test_fraud_ring_accounts_share_devices_and_merchants() -> None:
    transactions, _ = generate(1200, seed=4, profile="hard")
    ring = [tx for tx in transactions if tx.scenario == "fraud_ring"]
    assert ring
    assert len({tx.device_id for tx in ring}) <= 3
    assert len({tx.merchant_id for tx in ring}) <= 4
    assert len({tx.account_id for tx in ring}) > 5


def test_label_noise_flips_a_share_of_rows() -> None:
    clean, _ = generate(600, seed=5, profile="easy")
    noisy, _ = generate(600, seed=5, profile="easy", label_noise=0.2)
    flipped = sum(a.label != b.label for a, b in zip(clean, noisy, strict=True))
    assert 60 <= flipped <= 180, flipped


def test_benign_transactions_use_shared_devices() -> None:
    transactions, _ = generate(900, seed=6, profile="easy")
    hub_devices = {f"device_{index:04d}" for index in range(8)}
    benign_on_hub = {tx.device_id for tx in transactions if tx.label == 0} & hub_devices
    assert benign_on_hub, "shared devices must also carry legitimate traffic"


def test_hard_profile_changes_the_class_balance() -> None:
    easy, _ = generate(600, seed=7, profile="easy")
    hard, _ = generate(600, seed=7, profile="hard")
    easy_rate = sum(tx.label == 1 for tx in easy) / len(easy)
    hard_rate = sum(tx.label == 1 for tx in hard) / len(hard)
    assert hard_rate > easy_rate


def test_scenario_counts_are_reportable() -> None:
    transactions, _ = generate(500, seed=8, profile="hard")
    counts = Counter(tx.scenario for tx in transactions)
    assert sum(counts.values()) == 500
    assert counts["normal"] > 0


def test_generation_is_deterministic_per_profile() -> None:
    first, _ = generate(300, seed=9, profile="hard")
    second, _ = generate(300, seed=9, profile="hard")
    assert [tx.to_dict() for tx in first] == [tx.to_dict() for tx in second]
