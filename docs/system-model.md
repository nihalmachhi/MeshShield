# System model

## Purpose and boundary

MeshShield explores risk review for synthetic offline payment events. It sits beside a hypothetical payment system and never authorizes a transfer or changes settlement. A risk score is an input for a simulated analyst queue.

## Components and contracts

| Component | Module | Responsibility |
| --- | --- | --- |
| Synthetic generator | `generator.py` | Seeded transactions and sync events with documented scenarios. |
| Domain contracts | `domain.py` | Immutable transaction and sync event records with basic validation. |
| Feature pipeline | `features.py` | Point-in-time velocity and graph-derived features. |
| Integrity rules | `rules.py` | Deterministic duplicate, signature, and event-sequence checks. |
| Risk model | `model.py` | Standardized logistic regression and inspectable linear contributions. |
| Evaluation | `evaluation.py` | Imbalanced classification metrics and chronological holdout support. |
| Sync simulator | `simulator.py` | Duplicate delivery and deliberate out-of-order deliveries. |
| Storage | `storage.py` | JSON Lines datasets and SQLite event idempotency. |
| Pipeline | `pipeline.py` | Generation, fitting, evaluation, scoring, and artifact persistence. |
| API and UI | `web.py`, `frontend/index.html` | Local read-only review plus a replay demonstration route. |

## Event lifecycle

```text
synthetic transaction
        |
        v
offline device queue -- delayed / duplicate / out-of-order sync --> local ingestion
        |                                                        |
        +--> event_time history --> point-in-time features        +--> idempotency + integrity rules
                                       |                              |
                                       +--> model score ---------------+
                                                                      v
                                                          review queue and evidence
```

`event_time` describes transaction occurrence. `ingestion_time` describes observed arrival. Feature history is ordered by event time; delivery behavior is simulated separately. A duplicate event ID cannot be accepted a second time by the SQLite primary key.

## Storage and deployment choice

The MVP uses JSON Lines because the generated dataset is local, small, reproducible, and easy to inspect. SQLite provides a durable uniqueness constraint for sync events. The standard-library HTTP server keeps the demo self-contained and binds to loopback. PostgreSQL, Redis, a message broker, graph database, Kubernetes, and cloud deployment are omitted until measured scale or collaboration requirements justify the operational cost.

## Failure behavior

Malformed records fail validation rather than being silently repaired. Repeated IDs are surfaced as findings or ignored at sync ingestion. Invalid simulated signatures are rejected before idempotent acceptance. Model files and generated datasets can be recreated from a seed. The local demo server has no authentication and must not be exposed to a network.
