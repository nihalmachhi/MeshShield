from meshshield.data.generator import generate


def test_replay_scenario_reuses_a_prior_sync_event_id() -> None:
    transactions, _ = generate(300, seed=19)
    replay_events = [tx.event_id for tx in transactions if tx.scenario == "replay_attempt"]
    assert replay_events
    all_event_ids = [tx.event_id for tx in transactions]
    assert len(all_event_ids) > len(set(all_event_ids))
