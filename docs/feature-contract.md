# Feature contract

Feature construction is keyed by transaction ID and uses only prior events in event-time order. The row for a transaction is materialized before that transaction is added to any history collection. At equal timestamps, transaction ID provides deterministic ordering.

| Feature | Meaning at scoring time | Caution |
| --- | --- | --- |
| `log_amount` | Natural log of one plus the transaction amount. | Synthetic USD only. |
| `hour_sin`, `hour_cos` | Cyclical encoding of event hour. | UTC timestamps in this demo. |
| `account_velocity_1h` | Earlier transactions by this account in the trailing hour. | Event-time window, not arrival-time window. |
| `device_accounts_seen` | Distinct accounts previously seen on this device. | A relationship count, not proof of wrongdoing. |
| `merchant_velocity_1h` | Earlier transactions at this merchant in the trailing hour. | Synthetic merchant IDs. |
| `offline_duration_minutes` | Ingestion time minus event time, supplied by the simulator. | In a live system this field needs trustworthy clock and queue semantics. |
| `is_delayed_sync` | One when offline duration is at least 30 minutes. | A deterministic threshold, not fraud evidence by itself. |
| `account_transaction_count` | Prior transaction count for this account. | Starts at zero for the first event. |
| `account_device_degree` | Number of distinct devices previously used by this account. | Graph-derived feature; strictly historical and excludes the current device. |
| `device_recent_accounts_24h` | Distinct accounts using the device during the prior 24 hours. | Event-time window. |

Labels, scenario names, ingestion outcomes, review outcomes, settlement outcomes, and future history are excluded from the model feature vectors. The `scenario` field may be displayed for education and metric grouping only. Model contributions are signed input associations from a linear model; they are not causal explanations.
