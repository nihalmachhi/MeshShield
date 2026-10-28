import pytest

from meshshield.eval.metrics import evaluate


def test_evaluation_handles_zero_positives_and_rejects_mismatched_input():
    assert evaluate([0, 0], [0.1, 0.8])["pr_auc_average_precision"] == 0
    with pytest.raises(ValueError, match="same length"):
        evaluate([1], [])
