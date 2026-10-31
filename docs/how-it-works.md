# How it works

This is the short version of the pipeline, with a worked example. The contracts
are in [system-model.md](system-model.md); the numbers are in
[evaluation.md](evaluation.md).

## 1. Generate a stream

```powershell
$env:PYTHONPATH = "src"
python -m meshshield.cli generate --count 1600 --seed 2025 --profile easy
```

The generator writes `transactions.jsonl`, `sync_events.jsonl` and a dataset
card. Each transaction has a device-clock `event_time`, a server
`ingestion_time`, a signature and a scenario label. Delivery is shuffled so the
file order is arrival order, not event order.

## 2. Check integrity before scoring

```python
from meshshield.security.rules import inspect_transaction

findings = inspect_transaction(tx, seen_transaction_ids, seen_event_ids)
```

The rules are independent of the model:

| Finding | Cause |
| --- | --- |
| `invalid_simulated_signature` | The signature does not verify under the device key. |
| `duplicate_transaction_id` | The transaction ID was already accepted. |
| `replayed_event_id` | The sync event ID was already accepted. |
| `late_arrival` | The delay is above the gate threshold. |
| `event_time_in_future` | The device clock is ahead of the server clock. |

A finding sends the payment to review. The model score is still reported, but it
is not what caused the review.

## 3. Build features from the past only

```python
from meshshield.features.build import build_features, vector

rows = build_features(transactions)
values = vector(rows[transaction_id])          # graph features
values = vector(rows[transaction_id], False)   # transaction-only
```

Rows are sorted by `(event_time, transaction_id)`. Histories advance after every
transaction that shares a timestamp. If a transaction at 09:03 arrives after one
at 09:06, its features still use only events before 09:03. This is why a late
sync cannot leak the future into a training row.

## 4. Score and explain

```python
from meshshield.core.pipeline import load_or_prepare, score_transaction

transactions, metrics, model, calibrator, threshold = load_or_prepare()
result = score_transaction(tx, known, model, calibrator=calibrator, threshold=threshold)
```

The result separates evidence:

```json
{
  "risk_score": 0.87,
  "decision": "review",
  "integrity_findings": ["invalid_simulated_signature"],
  "top_contributions": [
    {"feature": "offline_duration_minutes", "contribution": 0.41}
  ],
  "evidence_types": {
    "integrity_findings": "direct simulation checks",
    "model_contributions": "model associations; not causal evidence"
  }
}
```

For logistic regression, contributions are `weight * (value - mean) / scale` and
add up to the logit apart from the bias, so they are an exact decomposition of
the score. For the tree and anomaly models they are empty on purpose: global
gain importance is not a per-row explanation.

## 5. Evaluate on a later slice

Training uses the earliest 80% of event time, then splits that period again into
fit and calibration. The latest 20% is the holdout. Nothing from the holdout is
used to choose features, weights, the calibrator or the threshold.

```powershell
python -m meshshield.cli train
python -m meshshield.cli evaluate
```

The run writes `metrics.json`, `calibration.json`, `ablation.json` and
`graph_summary.json` under `data/generated/`.

## 6. Simulate offline sync

```powershell
python -m meshshield.cli demo
```

`demo` generates, trains, and replays every sync event through an in-memory
SQLite store. The output counts accepted deliveries, ignored duplicates and
rejected signatures. The `serve` command does the same with a persistent store
and exposes `/api/replay`, which delivers one event twice.

## 7. Open the dashboard

```powershell
python -m meshshield.cli serve --host 127.0.0.1 --port 8000
```

The API is local and unauthenticated:

| Endpoint | Response |
| --- | --- |
| `GET /api/health` | Liveness and the synthetic-only flag. |
| `GET /api/metrics` | Saved metrics and sync summary. |
| `GET /api/transactions?limit=100` | Scored transactions with evidence. |
| `GET /api/transactions/{id}` | One transaction using only earlier rows. |
| `GET /api/ablation` | Nested feature-group results. |
| `GET /api/calibration` | Reliability bins and the threshold. |
| `GET /api/drift` | Population stability index per feature. |
| `POST /api/replay` | Delivers the same event twice. |

## A worked example

A device with a 3-minute fast clock creates a payment at 09:02 while offline. It
syncs at 09:51.

- Integrity: signature valid, event ID new, 49 minutes late → `late_arrival`
  (not blocking). The clock offset is inside the 15-minute contract.
- Features: account and merchant velocity use events before 09:02; the delay is
  49 minutes; the device's causal component contains the accounts already seen.
- Model: the delay and amount push the score up; the account's limited history
  pushes it down.
- Decision: if the calibrated score clears 0.82, the payment joins the review
  queue. The finding and the contributions stay in separate fields.

If the same event arrives twice, the second delivery is refused by SQLite and
counted as a duplicate. The features are not recomputed, because the event was
already part of history at its event time.
