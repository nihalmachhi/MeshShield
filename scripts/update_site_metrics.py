"""Update the landing-page results from the latest saved evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_FILE = ROOT / "site" / "index.html"
METRICS_FILE = ROOT / "data" / "generated" / "metrics.json"
START_MARKER = "<!-- metrics:start -->"
END_MARKER = "<!-- metrics:end -->"

MODELS = (
    ("graph_model", "Graph features · raw threshold"),
    ("graph_model_calibrated", "Graph features · calibrated"),
    ("non_graph_model", "Transaction only"),
    ("rule_only_baseline", "Rules only"),
    ("full_decision_pipeline", "Integrity-aware pipeline"),
)


def _metric(metrics: dict[str, Any], model_name: str, name: str) -> float:
    value = metrics[model_name][name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{model_name}.{name} must be numeric")
    if not 0 <= value <= 1:
        raise ValueError(f"{model_name}.{name} must be between 0 and 1")
    return float(value)


def render_results(metrics: dict[str, Any]) -> str:
    dataset = metrics["dataset"]
    test_count = dataset["test"]
    if isinstance(test_count, bool) or not isinstance(test_count, int) or test_count < 1:
        raise ValueError("dataset.test must be a positive integer")

    positive_count = metrics["graph_model"].get("positive_count")
    if isinstance(positive_count, bool) or not isinstance(positive_count, int):
        raise TypeError("graph_model.positive_count must be an integer")

    cards: list[str] = []
    for model_name, title in MODELS:
        precision = _metric(metrics, model_name, "precision")
        recall = _metric(metrics, model_name, "recall")
        f1 = _metric(metrics, model_name, "f1")
        average_precision = _metric(metrics, model_name, "pr_auc_average_precision")
        threshold = _metric(metrics, model_name, "threshold")
        cards.append(
            "\n".join(
                (
                    '<article class="card">',
                    f"<h3>{title}</h3>",
                    (
                        f"<p>Precision {precision:.2f}, recall {recall:.2f}, F1 {f1:.2f}. "
                        f"Threshold {threshold:.3f}.</p>"
                    ),
                    '<div class="viz">',
                    f'<div class="cap"><span style="width:{average_precision * 100:.1f}%"></span></div>',
                    f'<div class="leg">average precision {average_precision:.3f}</div>',
                    "</div>",
                    "</article>",
                )
            )
        )

    pipeline_note = (
        "The integrity-aware pipeline includes integrity findings alongside the model. "
        "Its result is not a model-only comparison."
    )
    return "\n".join(
        (
            '<div class="center">',
            "<h2>Measured on a later slice of time.</h2>",
            (
                f'<p class="lede">The saved run evaluates {test_count:,} synthetic payments, '
                f"including {positive_count:,} generated positive labels. Metrics below come from "
                "the latest event-time holdout.</p>"
            ),
            "</div>",
            '<div class="cards">',
            *cards,
            "</div>",
            (
                f'<p class="fine center" style="max-width:70ch;margin:18px auto 0">{pipeline_note} '
                "The graph-feature model does not outperform the transaction-only model on average "
                "precision in this run. Labels are generated scenarios, not verified fraud.</p>"
            ),
        )
    )


def update_site_metrics(site_path: Path = SITE_FILE, metrics_path: Path = METRICS_FILE) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    replacement = render_results(metrics)
    page = site_path.read_text(encoding="utf-8")
    if page.count(START_MARKER) != 1 or page.count(END_MARKER) != 1:
        raise ValueError("site must contain exactly one metrics marker pair")
    start = page.index(START_MARKER) + len(START_MARKER)
    end = page.index(END_MARKER)
    if start >= end:
        raise ValueError("metrics markers are out of order")
    site_path.write_text(page[:start] + "\n" + replacement + "\n" + page[end:], encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    update_site_metrics()
    print(f"Updated saved-run metrics in {SITE_FILE}")


if __name__ == "__main__":
    main()
