from meshshield.core.domain import SyncEvent
from meshshield.security.rules import inspect_event_order


def test_sync_order_checks_parsed_timestamps():
    regressed = SyncEvent(
        "e2", "b", "2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z", "test", 2, True
    )
    earlier = SyncEvent(
        "e1", "a", "2024-12-31T19:00:00-05:00", "2025-01-01T00:00:00Z", "test", 1, True
    )
    assert "event_time_regressed_with_sequence" not in inspect_event_order([earlier, regressed])
