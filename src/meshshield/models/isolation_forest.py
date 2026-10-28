"""Optional unsupervised anomaly scores using scikit-learn Isolation Forest."""

from typing import Any


def fit_isolation_forest(
    rows: list[list[float]], contamination: float = 0.01, random_seed: int = 2025
) -> Any:
    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be in (0, 0.5]")
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError as exc:
        raise RuntimeError(
            "Install MeshShield with the 'anomaly' extra to use Isolation Forest"
        ) from exc
    model = IsolationForest(contamination=contamination, random_state=random_seed, n_jobs=1)
    return model.fit(rows)
