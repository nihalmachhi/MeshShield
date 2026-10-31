# Evaluation

Every number on this page comes from the saved run described below. Nothing is
hand-entered from memory, and nothing is a claim about real fraud.

## Reproduce it

```powershell
$env:PYTHONPATH = "src"
python -m meshshield.cli demo
python -c "import json; print(json.load(open('data/generated/metrics.json'))['graph_model'])"
```

## Setup

| Item | Value |
| --- | --- |
| Generator profile | `easy` |
| Seed | `2025` |
| Rows | 1,600 (266 positive, 1,334 negative) |
| Split | earliest 80% train, latest 20% holdout |
| Fit / calibration | 1,024 / 256 rows inside the training period |
| Holdout | 320 rows, 56 positive |
| Model | standardized logistic regression |
| Calibration | Platt scaling fitted on the 256-row calibration slice |
| Review threshold | 0.820, chosen by the cost policy (FP=1, FN=5, capacity=10%) |
| Label source | generated scenarios, not verified fraud |

## Holdout results

Scores are the raw model output except for the calibrated row, which uses the
Platt slope and intercept saved in `calibration.json`.

| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC | P@10% | R@10% | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rules only | 0.647 | 0.440 | 0.524 | **0.709** | 0.905 | 0.625 | 0.400 | 0.079 |
| Transaction-only logistic | 0.537 | 0.880 | 0.667 | 0.545 | 0.920 | 0.531 | 0.340 | 0.109 |
| Graph logistic | 0.686 | 0.700 | 0.693 | 0.678 | 0.943 | 0.688 | 0.440 | 0.070 |
| Graph logistic, calibrated @ 0.820 | 0.765 | 0.260 | 0.388 | 0.678 | 0.943 | 0.688 | 0.440 | 0.071 |
| Full decision pipeline | 0.882 | 0.600 | **0.714** | **0.859** | **0.968** | **0.875** | **0.560** | **0.055** |

The full pipeline is the calibrated graph model with integrity findings forced
to review. P@10% and R@10% assume a reviewer can inspect the top tenth of the
queue.

### Paired bootstrap, 500 resamples

| Comparison | Point estimate | 95% interval |
| --- | --- | --- |
| Graph PR-AUC | 0.678 | 0.530 – 0.802 |
| Transaction-only PR-AUC | 0.545 | 0.411 – 0.671 |
| Rules PR-AUC | 0.709 | 0.590 – 0.804 |
| Full pipeline PR-AUC | 0.859 | 0.780 – 0.926 |
| Graph − transaction-only | +0.132 | +0.064 – +0.216 |
| Graph − rules | −0.031 | −0.174 – +0.107 |

The graph beats the transaction-only model on this profile, and the paired
interval excludes zero. It does **not** beat fixed rules on PR-AUC: that
difference is small and its interval crosses zero. On the harder profile below,
the graph gain disappears entirely. The honest summary is that the graph signal
is real but fragile, not that graph features solve the problem.

## Calibration

| Model | Expected calibration error (10 bins) |
| --- | --- |
| Full pipeline | 0.038 |
| Calibrated graph model | 0.042 |
| Raw graph model | 0.051 |
| Rules | 0.116 |
| Transaction-only | 0.147 |

Platt scaling reduces the calibration error on the holdout. The reliability bins
are saved under `evaluation_extras.calibration_curve_calibrated` in
`metrics.json` and served by `GET /api/calibration`.

Brier scores are reported for completeness, not as evidence of operational
calibration: the holdout is one small slice from one seed.

## Drift

`metrics.json` contains the population stability index (PSI) for every feature
between train and holdout. Values below 0.1 are usually treated as stable and
above 0.25 as a material shift. The simulator is stationary apart from the
slow-burn cohort, so most easy-profile PSI values are near zero. The dashboard
exposes the same numbers at `GET /api/drift`.

## The hard profile

The same command with `--profile hard --label-noise 0.02` changes the generator,
not the evaluation code. Test rows: 320, of which 120 are labelled positive.

| Model | Precision | Recall | PR-AUC | ROC-AUC |
| --- | --- | --- | --- | --- |
| Rules only | 0.816 | 0.592 | 0.829 | 0.827 |
| Transaction-only logistic | 0.733 | 0.892 | 0.911 | 0.919 |
| Graph logistic | 0.763 | 0.883 | 0.914 | 0.917 |
| Full decision pipeline | 0.961 | 0.408 | 0.895 | 0.914 |

The paired PR-AUC difference (graph − transaction-only) is +0.003 with a 95%
interval of −0.006 to +0.011. The rings and slow burns raise absolute scores for
every model but do not make the graph features clearly better. This is the most
important negative result in the project, and it is why the README does not
claim a graph win.

## Ablation

See [ablation.md](ablation.md). The short version: amount and time alone are a
strong baseline; adding graph features helps on the easy profile; the graph-only
group is weak on its own.

## Construct validity

These metrics measure recovery of *generated* scenarios. They do not measure
fraud detection. In particular:

- The generator draws from fixed scenarios with fixed weights. A real attacker
  would adapt.
- Labels are assigned by construction, so a model can recover an artifact of the
  generator rather than a behavioural pattern.
- The holdout has 56 positives. A single different row moves precision by about
  two points.
- Public datasets are supported for plumbing checks only (see
  `scripts/eval_public.py`); their labels, sampling and missing devices are not
  comparable to this generator.
