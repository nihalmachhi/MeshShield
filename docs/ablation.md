# Feature ablation

The ablation retrains the same logistic model on nested feature groups, with the
same seed and the same event-time split. It is written by every `train` / `demo`
run to `data/generated/ablation.json`.

Published run: easy profile, seed 2025, 1,600 rows, 320-row holdout with 56
positives.

| Feature group | Columns | PR-AUC | ROC-AUC | Precision | Recall |
| --- | --- | --- | --- | --- | --- |
| Amount and time | 3 | **0.844** | 0.886 | 0.571 | 0.800 |
| Velocity | 3 | 0.144 | 0.427 | 0.063 | 0.060 |
| Sync delay | 2 | 0.205 | 0.563 | 0.195 | 0.300 |
| Graph only | 7 | 0.209 | 0.485 | 0.300 | 0.120 |
| Transaction only | 9 | 0.545 | 0.920 | 0.537 | 0.880 |
| Graph full | 16 | 0.678 | 0.943 | 0.686 | 0.700 |

## Reading it

- **Amount and time carry most of the signal on this profile.** The generator
  draws high-amount and scenario amounts from visibly different distributions,
  so three columns recover much of the label. This is a generator artifact, not
  a finding about fraud.
- **Graph-only is weak.** In the easy profile, shared devices are mostly benign
  hubs (the 12% confounder), so graph structure alone is close to noise. A ROC of
  0.485 is at chance and is not a reason to trust or distrust the group; the
  holdout is small.
- **Graph features help in combination.** Moving from transaction-only (9
  columns) to graph-full (16 columns) raises PR-AUC from 0.545 to 0.678 and
  ROC-AUC from 0.920 to 0.943. The paired 95% interval for the PR-AUC difference
  is +0.064 to +0.216, which excludes zero on this run.
- **More columns are not monotonically better.** The 3-column model beats the
  16-column model on PR-AUC. Regularization, correlated counts and 1,024 training
  rows all contribute noise. A production system would select features on a
  validation slice and would need far more positives.

## The hard profile

With `--profile hard --label-noise 0.02`, the same ablation gives:

| Feature group | PR-AUC | ROC-AUC |
| --- | --- | --- |
| Amount and time | 0.916 | 0.908 |
| Velocity | 0.455 | 0.582 |
| Sync delay | 0.515 | 0.593 |
| Graph only | 0.552 | 0.619 |
| Transaction only | 0.911 | 0.919 |
| Graph full | 0.914 | 0.917 |

The graph gain disappears. The rings exist, but the per-row graph counts are
confounded by hub traffic and by the amount signal that dominates every group.
This negative result is reported rather than tuned away.

## Caveats

- One seed, one split. The bootstrap intervals in
  [evaluation.md](evaluation.md) show how wide the uncertainty is.
- The groups are nested but not orthogonal: velocity counts and graph counts are
  correlated by construction.
- No hyperparameter search is performed per group, so the comparison favors
  neither group deliberately but is still sensitive to the fixed regularization.
