import pytest

from meshshield.eval.calibration import fit_platt, select_cost_threshold
from meshshield.eval.drift import population_stability_index


def test_calibration_is_monotonic_and_threshold_respects_capacity() -> None:
    scores = [0.1, 0.2, 0.7, 0.9]
    calibrator = fit_platt(scores, [0, 0, 1, 1])
    calibrated = [calibrator.apply(score) for score in scores]
    assert calibrated == sorted(calibrated)
    choice = select_cost_threshold([0, 0, 1, 1], scores, 1.0, 5.0, 0.5)
    assert choice["review_rate"] <= 0.5


def test_drift_is_zero_for_same_distribution_and_rejects_empty_input() -> None:
    values = [0.0, 1.0, 2.0, 3.0]
    assert population_stability_index(values, values) == pytest.approx(0.0)
    with pytest.raises(ValueError):
        population_stability_index([], values)
