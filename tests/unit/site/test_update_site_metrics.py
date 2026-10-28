import json

import pytest

from scripts.update_site_metrics import render_results, update_site_metrics


def sample_metrics() -> dict[str, object]:
    model = {
        "precision": 0.75,
        "recall": 0.5,
        "f1": 0.6,
        "pr_auc_average_precision": 0.8,
        "threshold": 0.5,
    }
    return {
        "dataset": {"test": 10},
        "graph_model": {**model, "positive_count": 2},
        "graph_model_calibrated": model,
        "non_graph_model": model,
        "rule_only_baseline": model,
        "full_decision_pipeline": model,
    }


def test_render_results_labels_metrics_as_synthetic() -> None:
    result = render_results(sample_metrics())  # type: ignore[arg-type]

    assert "10 synthetic payments" in result
    assert "2 generated positive labels" in result
    assert "Transaction only" in result
    assert "integrity findings alongside the model" in result
    assert "not verified fraud" in result


def test_update_replaces_only_marked_section(tmp_path) -> None:
    page = tmp_path / "index.html"
    metrics = tmp_path / "metrics.json"
    page.write_text("before<!-- metrics:start -->old<!-- metrics:end -->after", encoding="utf-8")
    metrics.write_text(json.dumps(sample_metrics()), encoding="utf-8")

    update_site_metrics(page, metrics)

    content = page.read_text(encoding="utf-8")
    assert content.startswith("before<!-- metrics:start -->")
    assert content.endswith("<!-- metrics:end -->after")
    assert ">old<" not in content
    assert "average precision 0.800" in content


def test_update_rejects_missing_markers(tmp_path) -> None:
    page = tmp_path / "index.html"
    metrics = tmp_path / "metrics.json"
    page.write_text("missing markers", encoding="utf-8")
    metrics.write_text(json.dumps(sample_metrics()), encoding="utf-8")

    with pytest.raises(ValueError, match="metrics marker pair"):
        update_site_metrics(page, metrics)
