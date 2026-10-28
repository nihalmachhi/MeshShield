import pytest

from meshshield.security.signatures import generate_keypair, sign_payload, verify_payload


def test_ed25519_signature_verifies_canonical_payload_and_detects_changes() -> None:
    pytest.importorskip("cryptography")
    private_key, public_key = generate_keypair()
    payload = {"event_id": "event-1", "amount": 17}
    signature = sign_payload(payload, private_key)
    assert verify_payload(payload, signature, public_key)
    assert not verify_payload({**payload, "amount": 18}, signature, public_key)
