"""Optional XGBoost baseline for experiments on permitted tabular datasets."""

from typing import Any


def fit_xgboost(rows: list[list[float]], labels: list[int], random_seed: int = 2025) -> Any:
    if not rows or len(rows) != len(labels) or len(set(labels)) < 2:
        raise ValueError("XGBoost training needs matching rows and both label classes")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must contain only 0 or 1")
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("Install MeshShield with the 'boosted' extra to use XGBoost") from exc
    positives = sum(labels)
    negatives = len(labels) - positives
    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=negatives / positives if positives else 1.0,
        random_state=random_seed,
        n_jobs=1,
    )
    model.fit(rows, labels)
    return model
