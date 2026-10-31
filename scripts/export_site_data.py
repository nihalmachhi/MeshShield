"""Export the saved measured results into the React site's data module."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = PROJECT_ROOT / "data" / "generated" / "metrics.json"
OUTPUT_PATH = PROJECT_ROOT / "site" / "src" / "data" / "results.js"


def main() -> None:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    dataset = metrics["dataset"]
    model_keys = {
        "graph_model": "graph",
        "non_graph_model": "nonGraph",
        "rule_only_baseline": "rules",
        "full_decision_pipeline": "fullPipeline",
    }
    models = {}
    for metrics_key, site_key in model_keys.items():
        model = metrics[metrics_key]
        models[site_key] = {
            "precision": round(float(model["precision"]), 4),
            "recall": round(float(model["recall"]), 4),
            "f1": round(float(model["f1"]), 4),
            "prAuc": round(float(model["pr_auc_average_precision"]), 4),
            "rocAuc": round(float(model["roc_auc"]), 4),
            "brier": round(float(model["brier_score"]), 4),
        }
    source = {
        "generatedFrom": "data/generated/metrics.json",
        "dataset": {
            "transactions": int(dataset["transactions"]),
            "train": int(dataset["train"]),
            "calibration": int(dataset["calibration"]),
            "test": int(dataset["test"]),
            "positives": int(metrics["graph_model"]["positive_count"]),
        },
        "models": models,
        "threshold": float(metrics["threshold_policy"]["threshold"]),
        "evaluation": {
            "bootstrapResamples": int(
                metrics["evaluation_extras"]["bootstrap_95pct"]["pr_auc_graph"]["resamples"]
            ),
            "note": (
                "Percentile intervals over seeded resamples; the holdout is small, so intervals are wide."
            ),
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "export const results = "
        + json.dumps(source, indent=2, sort_keys=True)
        + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
