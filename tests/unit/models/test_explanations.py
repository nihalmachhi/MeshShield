import math

from meshshield.models.explanations import explain_logit
from meshshield.models.logistic import LogisticModel


def test_linear_attributions_reconstruct_model_logit() -> None:
    model = LogisticModel(("a", "b"), [1.0, 2.0], [2.0, 4.0], [0.5, -1.0], 0.25)
    result = explain_logit(model, [3.0, 6.0])
    assert result["logit"] == -0.25
    assert math.isclose(model.score([3.0, 6.0]), 1 / (1 + math.exp(-result["logit"])))
