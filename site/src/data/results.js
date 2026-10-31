export const results = {
  dataset: {
    calibration: 256,
    positives: 50,
    test: 320,
    train: 1024,
    transactions: 1600,
  },
  evaluation: {
    bootstrapResamples: 500,
    note: "Percentile intervals over seeded resamples; the holdout is small, so intervals are wide.",
  },
  generatedFrom: "data/generated/metrics.json",
  models: {
    fullPipeline: {
      brier: 0.0554,
      f1: 0.7143,
      prAuc: 0.8588,
      precision: 0.8824,
      recall: 0.6,
      rocAuc: 0.9677,
    },
    graph: {
      brier: 0.0704,
      f1: 0.6931,
      prAuc: 0.6778,
      precision: 0.6863,
      recall: 0.7,
      rocAuc: 0.9431,
    },
    nonGraph: {
      brier: 0.1085,
      f1: 0.6667,
      prAuc: 0.5454,
      precision: 0.5366,
      recall: 0.88,
      rocAuc: 0.9197,
    },
    rules: {
      brier: 0.079,
      f1: 0.5238,
      prAuc: 0.7091,
      precision: 0.6471,
      recall: 0.44,
      rocAuc: 0.9047,
    },
  },
  threshold: 0.8200622538329017,
};
