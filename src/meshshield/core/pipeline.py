"""End-to-end dataset, training, evaluation, and scoring orchestration."""

import json
import random
from typing import Any

from meshshield.config import (
    CALIBRATION_FILE,
    DATA_DIR,
    DEFAULT_SEED,
    DEFAULT_TRANSACTION_COUNT,
    EVENTS_FILE,
    FALSE_NEGATIVE_COST,
    FALSE_POSITIVE_COST,
    METRICS_FILE,
    MODEL_FILE,
    REVIEW_CAPACITY,
    TRANSACTIONS_FILE,
)
from meshshield.core.domain import SyncEvent, Transaction, parse_timestamp
from meshshield.data.generator import generate
from meshshield.data.storage import load_transactions, read_jsonl, write_jsonl
from meshshield.eval.calibration import PlattCalibrator, fit_platt, select_cost_threshold
from meshshield.eval.drift import population_stability_index
from meshshield.eval.metrics import evaluate, split_index
from meshshield.features.build import build_features, vector
from meshshield.models.logistic import LogisticModel, feature_names
from meshshield.security.rules import inspect_event_order, inspect_transaction


def generate_dataset(
    count: int = DEFAULT_TRANSACTION_COUNT, seed: int = DEFAULT_SEED
) -> dict[str, Any]:
    transactions, events = generate(count, seed)
    shuffled = list(zip(transactions, events))
    random.Random(seed).shuffle(shuffled)
    # Files model arrival order (not event-time order), preserving late syncs.
    write_jsonl(TRANSACTIONS_FILE, (tx.to_dict() for tx, _ in shuffled))
    write_jsonl(EVENTS_FILE, (event.to_dict() for _, event in shuffled))
    card = {
        "dataset_name": "meshshield_synthetic_offline_payments",
        "version": 1,
        "seed": seed,
        "transaction_count": count,
        "positive_count": sum(tx.label == 1 for tx in transactions),
        "scenarios": {
            scenario: sum(tx.scenario == scenario for tx in transactions)
            for scenario in sorted({tx.scenario for tx in transactions})
        },
        "data_origin": "synthetically generated; no real personal or payment data",
        "ground_truth": "scenario labels assigned by the simulator, not verified fraud outcomes",
        "limitations": [
            "Synthetic patterns are simplified and may not match real fraud.",
            "Metrics measure recovery of generator labels only.",
            "Not validated for live payment or account decisions.",
        ],
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "dataset_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card


def _rule_score(tx: Transaction, features: dict[str, float]) -> float:
    if not tx.signature_valid:
        return 1.0
    score = 0.0
    if tx.amount >= 250:
        score += 0.35
    if tx.offline_duration_minutes >= 30:
        score += 0.15
    if features["device_accounts_seen"] >= 4:
        score += 0.45
    if features["account_velocity_1h"] >= 3:
        score += 0.25
    return min(score, 1.0)


def train_and_evaluate() -> dict[str, Any]:
    transactions = load_transactions(TRANSACTIONS_FILE)
    if len(transactions) < 100:
        raise ValueError("Dataset missing or too small. Run `meshshield generate` first.")
    features = build_features(transactions)
    # Time split by event time, with all graph history constructed causally.
    ordered = sorted(
        transactions, key=lambda tx: (parse_timestamp(tx.event_time), tx.transaction_id)
    )
    cut = split_index(len(ordered))
    train, test = ordered[:cut], ordered[cut:]
    calibration_cut = split_index(len(train), 0.8)
    model_train, calibration = train[:calibration_cut], train[calibration_cut:]
    labels_train = [int(tx.label or 0) for tx in model_train]
    graph_model = LogisticModel.fit(
        [vector(features[t.transaction_id]) for t in model_train], labels_train, feature_names(True)
    )
    base_model = LogisticModel.fit(
        [vector(features[t.transaction_id], graph=False) for t in model_train],
        labels_train,
        feature_names(False),
    )
    labels_calibration = [int(tx.label or 0) for tx in calibration]
    calibration_scores = [
        graph_model.score(vector(features[t.transaction_id])) for t in calibration
    ]
    calibrator = fit_platt(calibration_scores, labels_calibration)
    threshold_policy = select_cost_threshold(
        labels_calibration,
        [calibrator.apply(score) for score in calibration_scores],
        FALSE_POSITIVE_COST,
        FALSE_NEGATIVE_COST,
        REVIEW_CAPACITY,
    )
    y_test = [int(tx.label or 0) for tx in test]
    graph_scores = [graph_model.score(vector(features[t.transaction_id])) for t in test]
    calibrated_scores = [calibrator.apply(score) for score in graph_scores]
    base_scores = [base_model.score(vector(features[t.transaction_id], graph=False)) for t in test]
    rule_scores = [_rule_score(t, features[t.transaction_id]) for t in test]
    # Integrity checks run in ingestion order so only already-arrived events count.
    test_ids = {tx.transaction_id for tx in test}
    graph_score_by_id = {tx.transaction_id: score for tx, score in zip(test, graph_scores)}
    seen_tx_ids: set[str] = set()
    seen_event_ids: set[str] = set()
    pipeline_labels: list[int] = []
    pipeline_scores = []
    for tx in sorted(
        transactions, key=lambda item: (parse_timestamp(item.ingestion_time), item.transaction_id)
    ):
        findings = inspect_transaction(tx, seen_tx_ids, seen_event_ids)
        if tx.transaction_id in test_ids:
            pipeline_labels.append(int(tx.label or 0))
            score = calibrator.apply(graph_score_by_id[tx.transaction_id])
            pipeline_scores.append(1.0 if findings else score)
        seen_tx_ids.add(tx.transaction_id)
        seen_event_ids.add(tx.event_id)
    ordered_events = load_events()
    metrics = {
        "dataset": {
            "transactions": len(transactions),
            "train": len(model_train),
            "calibration": len(calibration),
            "test": len(test),
            "split": "event-time 80/20 holdout; earlier period split 80/20 fit/calibration",
            "label_source": "synthetic scenario",
        },
        "graph_model": evaluate(y_test, graph_scores),
        "graph_model_calibrated": evaluate(
            y_test, calibrated_scores, threshold_policy["threshold"]
        ),
        "non_graph_model": evaluate(y_test, base_scores),
        "rule_only_baseline": evaluate(y_test, rule_scores),
        "full_decision_pipeline": evaluate(
            pipeline_labels, pipeline_scores, threshold_policy["threshold"]
        ),
        "sync_event_order_findings": inspect_event_order(ordered_events),
        "feature_drift_psi": {
            name: population_stability_index(
                [features[tx.transaction_id][name] for tx in train],
                [features[tx.transaction_id][name] for tx in test],
            )
            for name in feature_names(True)
        },
        "threshold_policy": {
            **threshold_policy,
            "false_positive_cost": FALSE_POSITIVE_COST,
            "false_negative_cost": FALSE_NEGATIVE_COST,
            "review_capacity": REVIEW_CAPACITY,
            "calibration_samples": len(calibration),
        },
        "threshold_note": "The cost weights and capacity are explicit demo assumptions, not operational recommendations.",
    }
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    graph_model.save(MODEL_FILE)
    base_model.save(DATA_DIR / "baseline_model.json")
    CALIBRATION_FILE.write_text(
        json.dumps(
            {
                "slope": calibrator.slope,
                "intercept": calibrator.intercept,
                "threshold": threshold_policy["threshold"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def load_events() -> list[SyncEvent]:
    return [SyncEvent(**row) for row in read_jsonl(EVENTS_FILE)]


def load_or_prepare() -> tuple[
    list[Transaction], dict[str, Any], LogisticModel, PlattCalibrator, float
]:
    if not TRANSACTIONS_FILE.exists():
        generate_dataset()
    if not MODEL_FILE.exists() or not METRICS_FILE.exists() or not CALIBRATION_FILE.exists():
        train_and_evaluate()
    calibration = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
    return (
        load_transactions(TRANSACTIONS_FILE),
        json.loads(METRICS_FILE.read_text(encoding="utf-8")),
        LogisticModel.load(MODEL_FILE),
        PlattCalibrator(calibration["slope"], calibration["intercept"]),
        calibration["threshold"],
    )


def score_transaction(
    tx: Transaction,
    known: list[Transaction],
    model: LogisticModel,
    feature_rows: dict[str, dict[str, float]] | None = None,
    seen_transaction_ids: set[str] | None = None,
    seen_event_ids: set[str] | None = None,
    calibrator: PlattCalibrator | None = None,
    threshold: float = 0.5,
) -> dict[str, Any]:
    if feature_rows is None:
        feature_rows = build_features(known + [tx])
    row = feature_rows[tx.transaction_id]
    probability = model.score(vector(row))
    if calibrator is not None:
        probability = calibrator.apply(probability)
    seen_tx = (
        seen_transaction_ids
        if seen_transaction_ids is not None
        else {item.transaction_id for item in known}
    )
    seen_events = (
        seen_event_ids if seen_event_ids is not None else {item.event_id for item in known}
    )
    findings = inspect_transaction(tx, seen_tx, seen_events)
    # Integrity failures are surfaced independently from the ML score.
    reason_map = {
        "invalid_simulated_signature": "The simulated signature check failed.",
        "duplicate_transaction_id": "This transaction identifier was already observed.",
        "replayed_event_id": "This sync event identifier was already observed.",
    }
    contributions = model.contributions(vector(row))
    reasons = [reason_map[item] for item in findings if item in reason_map]
    reasons.extend(
        f"{str(item['feature']).replace('_', ' ')} contributed to the model score"
        for item in contributions
        if float(item["contribution"]) > 0
    )
    return {
        "transaction_id": tx.transaction_id,
        "risk_score": round(probability, 4),
        "risk_percent": round(probability * 100, 1),
        "decision": "review" if findings or probability >= threshold else "low_risk",
        "integrity_findings": findings,
        "top_contributions": contributions,
        "review_reasons": reasons[:5],
        "evidence_types": {
            "integrity_findings": "direct simulation checks",
            "model_contributions": "model associations; not causal evidence",
        },
        "feature_values": row,
    }
