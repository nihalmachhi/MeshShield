# Synthetic data card

## Origin and generation

- Dataset name: `meshshield_synthetic_offline_payments`, version 1.
- Default size: 1,600 transactions; default seed: 2025.
- Time origin: January 2025 in UTC, with event times and delayed arrival times.
- Actors: generated account, device, and merchant identifiers; no real personal or payment data.
- Labels: scenario labels assigned by the simulator. They indicate injected patterns, not confirmed fraud.
- Persistence: `data/generated/transactions.jsonl`, `sync_events.jsonl`, and `dataset_card.json`.

## Scenarios

| Scenario | Label | Simulation pattern |
| --- | --- | --- |
| `normal` | 0 | Typical generated amount, account/device assignment, and sync delay. |
| `high_amount` | 1 | Larger amount drawn from an elevated range. |
| `shared_device` | 1 | Multiple accounts are assigned to a small device pool. |
| `replay_attempt` | 1 | Longer offline delay; sync event may be delivered more than once by the transport simulator. |
| `invalid_signature` | 1 | Signature verification outcome is false in the simulation. |

The default generator selects the normal scenario roughly 84% of the time; the scenario mixture is controlled in `generator.py`. Sampling and overlaps are stochastic. Always read counts from the generated dataset card rather than assuming exact proportions.

## Intended use

Education, local demos, feature pipeline development, and repeatable code experiments. Not suitable for training a real payment fraud model, measuring real-world fraud rates, asserting fairness, or making financial decisions.

## Known limitations

The generator has a small fixed actor population and hand-authored scenario patterns. Labels are perfectly linked to those scenario definitions. Real activity is more diverse, adaptive, and ambiguous. The distribution has no independently adjudicated outcomes, protected-group assessment, or real deployment feedback. Dataset size and model scores are demonstrations only.
