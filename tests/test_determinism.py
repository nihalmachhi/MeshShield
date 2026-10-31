"""Same seed, same bytes. Reproducibility is a feature, not a hope."""

from __future__ import annotations

import hashlib
from pathlib import Path

from meshshield.core.pipeline import generate_dataset


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_same_seed_produces_byte_identical_files(isolated_paths: dict[str, Path]) -> None:
    generate_dataset(200, seed=2025)
    first_transactions = _digest(isolated_paths["transactions"])
    first_events = _digest(isolated_paths["events"])

    generate_dataset(200, seed=2025)
    assert _digest(isolated_paths["transactions"]) == first_transactions
    assert _digest(isolated_paths["events"]) == first_events


def test_a_different_seed_changes_the_dataset(isolated_paths: dict[str, Path]) -> None:
    generate_dataset(200, seed=2025)
    first = _digest(isolated_paths["transactions"])
    generate_dataset(200, seed=2026)
    assert _digest(isolated_paths["transactions"]) != first


def test_dataset_card_records_the_seed_and_counts(isolated_paths: dict[str, Path]) -> None:
    from conftest import read_json

    from meshshield.data.storage import read_jsonl

    card = generate_dataset(150, seed=77)
    rows = list(read_jsonl(isolated_paths["transactions"]))
    assert card["seed"] == 77
    assert card["transaction_count"] == 150
    assert card["positive_count"] == sum(1 for row in rows if row["label"] == 1)
    assert read_json(isolated_paths["card"])["seed"] == 77
