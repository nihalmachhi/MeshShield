# Evaluation protocol

## Split and comparisons

The pipeline sorts transactions by event time and assigns the first 80% to training and the later 20% to holdout evaluation. The feature pipeline is causal: each row uses only prior event-time transactions. This split checks a later synthetic period, but it does not test a genuinely new population or real-world distribution.

The model-fit period is split again chronologically: the earlier 80% fits the model and the later 20% calibrates its scores and selects a review threshold. The final 20% remains untouched until evaluation. Three existing methods are compared:

1. `graph_model`: logistic regression with transaction and relationship features.
2. `non_graph_model`: same training setup with transaction, velocity, and delay features but without graph-derived inputs.
3. `rule_only_baseline`: hand-authored thresholds for high amounts, long delay, shared device, and account velocity, with invalid signatures treated as a direct integrity issue.

Metrics include precision, recall, F1, average precision (PR-AUC approximation), Brier score, confusion counts, and review rate. Accuracy is omitted because the generated labels are imbalanced. The Platt calibrator is fit only on the calibration interval. A threshold is selected on that interval under an explicit 10% review-capacity assumption and illustrative false-positive: false-negative costs of 1:5. These costs are example inputs, not researched operational values.

The report includes a calibrated graph-feature logistic baseline, the original raw model, and an integrity-aware pipeline. It also reports per-feature population stability index (PSI) between the training and test periods. A drift score flags a change to investigate; it is not a quality or fairness verdict. The additive model explanation is exact on the fitted model's logit scale around training feature means. It assumes independent feature attribution and is not causal evidence.

## Reading the results

Generated metrics are written to `data/generated/metrics.json` after `demo` or `train`. They describe recovery of the generator's synthetic labels only. Any superiority of one method can reflect deliberate synthetic patterns, not an advantage that transfers to actual payment fraud. Compare review volume and false positives at an explicit analyst capacity before discussing operational usefulness.

## Measured synthetic run

This is one local run of seed `2025` on the built-in generator, not a real-data benchmark. It used 1,600 rows: 1,024 for fitting, 256 for calibration, and 320 for the final holdout; 51 holdout labels were positive.

| Holdout result | Raw graph-feature logistic | Calibrated model and selected threshold | Integrity-aware pipeline |
| --- | ---: | ---: | ---: |
| Threshold | 0.5000 | 0.8797 | 0.8797 |
| Average precision | 0.8689 | 0.8689 | 0.9501 |
| Brier score | 0.0963 | 0.0576 | 0.0547 |
| Precision | 0.5618 | 0.8788 | 0.9111 |
| Recall | 0.9804 | 0.5686 | 0.8039 |
| Review rate | 27.81% | 10.31% | 14.06% |

The calibration interval selected a 9.77% review rate under the 10% cap and the illustrative 1:5 cost ratio. The final holdout review rate was 10.31%, showing that capacity does not transfer exactly across periods. The pipeline's higher average precision is due in part to simulator integrity signals linked to generator scenarios; it should not be read as a stronger production model.

## Current gaps

- No cross-validation, confidence intervals, independent labels, or real-world validation.
- No subgroup analysis, uncertainty intervals, unseen-pattern evaluation, or adversarial adaptation experiment.
- No externally supplied dataset has been downloaded or evaluated in this repository. See [public dataset terms and adapters](public-datasets.md).
- The generator and its labels are known; scenario holdout must be added before making stronger generalization claims.
- No throughput benchmark has been measured.

Use the stored seed and dataset card to reproduce the demo. Report actual generated counts and metrics; do not copy example numbers from a prior run.
