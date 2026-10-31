# Feature contract

Every feature is defined here with its window, its inputs and the argument for why
it cannot see the future. If a feature is added without an entry in this table,
the leakage tests are the only thing standing between the project and a number
that means nothing.

The contract lives in `src/meshshield/config.py` as `FEATURES` (transaction-only)
and `GRAPH_FEATURES` (`FEATURES` plus graph structure). Labels (`label`,
`scenario`), identifiers and signature fields are never features.

## The ordering rule

Features are computed per transaction from events whose `event_time` is
**strictly earlier** than the transaction's own `event_time`. Events with an equal
timestamp are invisible to each other. Delivery order is irrelevant.

Implementation: `src/meshshield/features/build.py` sorts by
`(event_time, transaction_id)`, groups equal timestamps, computes every row in a
group before appending any member to history, then advances the histories.

Proofs: `tests/test_features_no_leakage.py`, `tests/test_out_of_order_sync.py`.

## Transaction-only features

| Feature | Definition | Window | Leakage argument |
| --- | --- | --- | --- |
| `log_amount` | `log1p(amount)` | The row itself | Amount is captured at event time. |
| `hour_sin`, `hour_cos` | Cyclical encoding of the device-clock hour | The row itself | Uses the device clock, which is available at event time. |
| `account_velocity_1h` | Count of earlier events for the same account | `[t-1h, t)` | Only earlier events enter the deque. |
| `merchant_velocity_1h` | Count of earlier events for the same merchant | `[t-1h, t)` | Same deque rule. |
| `device_accounts_seen` | Distinct accounts seen on the device | All earlier events | Set is updated after the timestamp group. |
| `offline_duration_minutes` | `ingestion_time - event_time` | The row itself | Known when the event arrives. |
| `is_delayed_sync` | `offline_duration_minutes >= 30` | The row itself | Derived from the field above. |
| `account_transaction_count` | Count of earlier events for the account | All earlier events | Counter incremented after the group. |
| `account_device_degree` | Distinct devices used by the account | All earlier events | Set updated after the group. |
| `device_recent_accounts_24h` | Distinct accounts on the device | `[t-24h, t)` | Deque pruned at `t`, updated after the group. |

## Graph features

| Feature | Definition | Window | Leakage argument |
| --- | --- | --- | --- |
| `graph_component_size` | Size of the account–device–merchant component containing the account, built only from earlier events | All earlier events | Components are rebuilt from the causal snapshot at `t`. |
| `graph_two_hop_size` | Nodes within two hops of the account in the causal graph | All earlier events | Same snapshot. |
| `graph_account_degree` | Number of graph neighbours of the account | All earlier events | Same snapshot. |
| `graph_device_degree` | Number of graph neighbours of the device | All earlier events | Same snapshot. |
| `graph_pagerank` | PageRank of the account in the causal snapshot | All earlier events | Optional, requires `networkx`; absent values are written as `0.0` and flagged in `docs/evaluation.md`. |
| `graph_community_id` | Community label (label propagation) of the account | All earlier events | Optional, requires `networkx`. |

The graph is maintained **incrementally**: edges from a timestamp group are added
after that group's rows are computed. Building one global graph and looking up a
past transaction is the classic leak this design rejects.

## Clock-skew policy

The generator gives every device a fixed offset (sampled around zero) plus a slow
drift. `event_time` is the **device clock**, never true time.

| Situation | Finding | Blocking? | Rationale |
| --- | --- | --- | --- |
| `event_time > ingestion_time` (within 15 minutes) | `event_time_in_future` | Yes | The event claims a future the server has not reached. |
| `event_time > ingestion_time` by more than 15 minutes | rejected by the contract | n/a | Not a skew, a malformed record. |
| Offset deviates by more than 15 minutes from the device's rolling median | `device_clock_drift` | No | Quality signal for review, not proof of fraud. |
| Arrival delay above the gate threshold | `late_arrival` | No | Late events are normal in offline mode. |
| Key revoked, but the signature was made before revocation | `late_after_revocation` | No | The signature was valid when produced. |

The offset estimate is the rolling median of `ingestion_time - event_time` per
device, capped at the last 50 observations
(`src/meshshield/security/integrity.py::ClockSkewEstimator`).

## Model inputs

| Model | Feature set |
| --- | --- |
| `rules` | No features; deterministic thresholds over amount, delay, device and velocity. |
| `logistic` | `FEATURES` |
| `logistic-graph` | `GRAPH_FEATURES` |
| `isolation-forest` | `GRAPH_FEATURES`, unsupervised (`boost` extra) |
| `lightgbm` | `GRAPH_FEATURES` (`boost` extra) |

All models share one chronological split. Calibration is fitted inside the
training period, never on the holdout.
