from meshshield.sync.replication import merge_event_sets


def test_event_set_merge_is_idempotent_and_quarantines_payload_conflicts() -> None:
    original = {"event_id": "e1", "amount": 10}
    conflict = {"event_id": "e1", "amount": 11}
    merged = merge_event_sets([original], [original])
    assert len(merged.events) == 1
    assert not merged.conflicting_event_ids
    conflicted = merge_event_sets([original], [conflict])
    assert conflicted.conflicting_event_ids == ("e1",)
    assert conflicted == merge_event_sets([conflict], [original])
