# System model

MeshShield is a simulator, not a payment processor. This document describes what
the pieces are, how they fit together, and which invariants the code is allowed
to promise.

## One transaction, two clocks

A payment is created on a device that may be offline. It carries:

| Field | Meaning |
| --- | --- |
| `event_time` | The device clock when the payment was created. |
| `ingestion_time` | The server clock when the sync arrived. |
| `offline_duration_minutes` | `ingestion_time - event_time`, never negative. |
| `device_counter` | Monotonic per-device sequence, used to detect skipped events. |
| `key_id`, `signature` | Which device key signed the payload, and the signature bytes. |

`event_time` is the ordering key for history and for the train/test split.
`ingestion_time` is only used for integrity checks and for the review queue. A
late sync therefore cannot rewrite what the model knew at the time of the event.

`Transaction.validate()` rejects negative amounts, negative delays, invalid
labels, and an `event_time` more than 15 minutes *ahead* of `ingestion_time`.
Small forward skew is legitimate and is surfaced as an integrity finding instead
of being silently corrected.

## Pipeline stages

```
generate -> integrity -> point-in-time features -> model -> decision
                |                |                    |
          findings          feature rows         calibrated score
```

1. **Generate** (`data/generator.py`) creates a seeded synthetic stream in two
   profiles. Every event is signed with a per-device simulated key and a clock
   offset.
2. **Integrity** (`security/rules.py`, `security/integrity.py`) runs deterministic
   checks. Duplicate transaction IDs, replayed event IDs, invalid signatures,
   impossible event times and revoked keys are findings. Findings are not model
   output and can send a payment to review on their own.
3. **Features** (`features/build.py`) computes each row from strictly earlier
   `event_time`s. Same-timestamp peers are invisible to each other. Graph state
   is updated after a timestamp group, never before.
4. **Model** (`models/registry.py`) produces a score in `[0, 1]`. Logistic
   regression exposes additive per-row contributions. LightGBM and Isolation
   Forest are available but deliberately report no per-row attribution.
5. **Decision** (`core/pipeline.py`) combines findings and a calibrated score
   against a review threshold chosen on an earlier calibration slice.

## Module map

| Path | Responsibility |
| --- | --- |
| `src/meshshield/config.py` | Paths, seeds, feature lists, cost assumptions. |
| `src/meshshield/core/domain.py` | Frozen `Transaction` and `SyncEvent` contracts. |
| `src/meshshield/core/pipeline.py` | Orchestration, split, ablation, metrics files. |
| `src/meshshield/data/` | Generator, JSONL storage, SQLite, public adapters. |
| `src/meshshield/features/` | Causal row features and snapshot graph reports. |
| `src/meshshield/models/` | Logistic, LightGBM wrapper, Isolation Forest, registry. |
| `src/meshshield/eval/` | Metrics, calibration, drift, public evaluation. |
| `src/meshshield/security/` | Rules, signatures, replay window, clock skew. |
| `src/meshshield/sync/` | Delivery simulation and idempotent ingestion. |
| `src/meshshield/api/` | Local JSON API and static site server. |
| `site/` | Vite + React landing page and browser simulator. |

## State and persistence

- JSONL files (`data/generated/`) hold the reproducible dataset, events and
  metrics. They are regenerated from the seed and are not committed.
- SQLite holds accepted event IDs. `IdempotencyStore.accept()` returns `False`
  for a retry, and the row is counted as a duplicate.
- `model.json` is a plain JSON model. Older files without a `kind` field are read
  as logistic models.
- Nothing reads the wall clock. Every timestamp comes from the seed or from the
  caller.

## What the system promises

- Same seed, same code, same data: identical events, features, scores and
  metrics. Tests cover this.
- History is causal by `event_time`, regardless of arrival order or duplication.
- Integrity findings and model contributions are reported in separate fields.
- Every metric in the README and site comes from a saved local run.

## What it does not promise

- That synthetic labels mean fraud.
- That a threshold, feature or model would survive contact with real traffic.
- That the graph features are useful. The ablation in `docs/ablation.md` shows a
  gain on the easy profile and no measurable gain on the hard profile.
- That the local API is safe to expose. It has no authentication and binds to
  loopback by default.
