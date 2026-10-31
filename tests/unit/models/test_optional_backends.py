from importlib.util import find_spec

import pytest

from meshshield.models.graph_sage import fit_graph_sage
from meshshield.models.xgboost_model import fit_xgboost


@pytest.mark.parametrize(
    ("dependency", "call", "message"),
    [
        ("torch_geometric", lambda: fit_graph_sage(None, None, None, None), "'graph' extra"),
        ("xgboost", lambda: fit_xgboost([[0.0], [1.0]], [0, 1]), "'boosted' extra"),
    ],
)
def test_optional_backends_fail_with_install_hint(dependency, call, message) -> None:
    if find_spec(dependency) is not None:
        pytest.skip(f"{dependency} is installed; this checks the missing-extra message")
    with pytest.raises(RuntimeError, match=message):
        call()
