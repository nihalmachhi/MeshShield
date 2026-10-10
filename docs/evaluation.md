# Evaluation protocol

## Split and comparisons

The pipeline sorts transactions by event time and assigns the first 80% to training and the later 20% to holdout evaluation. The feature pipeline is causal: each row uses only prior event-time transactions. This split checks a later synthetic period, but it does not test a genuinely new population or real-world distribution.

Three methods are compared at the demonstration threshold of 0.5:

1. `graph_model`: logistic regression with transaction and relationship features.
2. `non_graph_model`: same training setup with transaction, velocity, and delay features but without graph-derived inputs.
3. `rule_only_baseline`: hand-authored thresholds for high amounts, long delay, shared device, and account velocity, with invalid signatures treated as a direct integrity issue.

Metrics include precision, recall, F1, average precision (PR-AUC approximation), Brier score, confusion counts, and review rate. Accuracy is omitted because the generated labels are imbalanced. The Brier score is a probability error summary, not evidence that scores are calibrated.

## Reading the results

Generated metrics are written to `data/generated/metrics.json` after `demo` or `train`. They describe recovery of the generator's synthetic labels only. Any superiority of one method can reflect deliberate synthetic patterns, not an advantage that transfers to actual payment fraud. Compare review volume and false positives at an explicit analyst capacity before discussing operational usefulness.

## Current gaps

- No cross-validation, confidence intervals, independent labels, or real-world validation.
- No capacity-constrained threshold selection or subgroup analysis.
- No model drift, unseen-pattern, calibration, or adversarial adaptation experiment.
- The generator and its labels are known; scenario holdout must be added before making stronger generalization claims.
- No throughput benchmark has been measured.

Use the stored seed and dataset card to reproduce the demo. Report actual generated counts and metrics; do not copy example numbers from a prior run.
