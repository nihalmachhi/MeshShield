# Synthetic data

MeshShield never uses real payments, real people or real fraud labels. Every row
is produced by `src/meshshield/data/generator.py` from a seed, and the dataset
card (`data/generated/dataset_card.json`) records how.

## Profiles

### `easy`

The original generator: independent scenarios drawn from fixed weights.

| Scenario | Weight | What it does |
| --- | --- | --- |
| `normal` | 84 | Ordinary payments, 12% of which share a benign hub device. |
| `high_amount` | 4 | Amount between 250 and 950. |
| `shared_device` | 5 | Several accounts on one hub device. |
| `replay_attempt` | 3 | Reuses an earlier event ID or signature. |
| `invalid_signature` | 4 | Flips bytes in the simulated signature. |

### `hard`

Adds adversarial structure and a label-noise option.

| Scenario | Weight | What it does |
| --- | --- | --- |
| `fraud_ring` | 7 | Twelve accounts share three devices and four merchants. |
| `slow_burn` | 5 | A twelve-account cohort stays quiet, then bursts after 70% of the window. |
| `structuring` | 6 | Amounts between 232 and 249, just under the 250 rule. |
| `device_rotation` | 4 | One account spreads activity across many devices. |
| `shared_device` | 5 | Still present, and still confounded by benign hubs. |

`--label-noise 0.02` flips 2% of labels. Label noise uses its own RNG stream, so
turning it on does not change the underlying events.

## Time and signatures

- Events are spaced eight minutes apart with up to seven minutes of jitter, over
  a synthetic January 2025 window.
- Every device has a fixed clock offset (normal, σ = 2.5 minutes) and a slow
  drift of up to 40 ppm. `event_time` is the device clock.
- 22% of events are delayed; replay and slow-burn scenarios are always delayed.
- Every transaction is signed with a simulated per-device key. Tampering flips
  bytes, so the signature check fails without any real cryptography. An Ed25519
  signer is available with the `crypto` extra.

## Class balance

The easy profile at 1,600 rows produces 266 positives (16.6%). The hard profile
with 2% label noise produces proportionally more positives and a noisier label.
The dataset card reports the exact counts, the profile, the seed and per-scenario
counts.

## Reproducibility

```powershell
$env:PYTHONPATH = "src"
python -m meshshield.cli generate --count 1600 --seed 2025 --profile hard --label-noise 0.02
python -m meshshield.cli train
```

The same command produces byte-identical JSONL on the same Python version. Tests
assert that generation, features and metrics are stable from the seed.

## Blind spots

The dataset card lists what the generator cannot model:

- Attackers do not adapt to the detector; scenarios are static draws.
- There are no refunds, chargebacks, disputes, merchant risk or issuer behaviour.
- There is no cross-border, multi-currency or regulatory structure.
- Clock skew is a seeded model, not measured from hardware.
- Ring structure is explicit and learnable; real collusion is not this clean.

## Why publish the generator anyway

A synthetic stream makes leakage, ordering and integrity testable in ways that a
real dataset cannot: the true event order is known, tampering can be inserted on
purpose, and the same seed reproduces a failure. The cost is that every metric
is a measurement of the generator, not of fraud. The README and
[evaluation.md](evaluation.md) say so in every table.
