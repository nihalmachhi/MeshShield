import pytest

from meshshield.core.domain import parse_timestamp


def test_timestamp_requires_timezone_and_normalizes_to_utc():
    assert parse_timestamp("2025-01-01T01:00:00+01:00") == parse_timestamp("2025-01-01T00:00:00Z")
    with pytest.raises(ValueError):
        parse_timestamp("2025-01-01T00:00:00")
