import pytest

from meshshield.federated.aggregation import federated_average


def test_federated_average_weights_updates_by_local_sample_count() -> None:
    assert federated_average([[1.0, 2.0], [3.0, 4.0]], [1, 3]) == [2.5, 3.5]
    with pytest.raises(ValueError):
        federated_average([[1.0], [2.0, 3.0]], [1, 1])
