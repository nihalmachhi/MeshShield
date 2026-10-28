import pytest

from meshshield.models.logistic import LogisticModel


def test_model_uses_class_weights_and_converges():
    model = LogisticModel.fit([[0.0], [1.0], [2.0], [3.0]], [0, 0, 0, 1], ("x",), epochs=1000)
    assert model.score([3.0]) > model.score([0.0])
    with pytest.raises(ValueError, match="feature vector"):
        model.score([1.0, 2.0])
