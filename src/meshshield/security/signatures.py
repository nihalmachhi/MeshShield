"""Optional Ed25519 signing for canonical sync payloads."""

import base64
import json
from typing import Any


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def generate_keypair() -> tuple[bytes, bytes]:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        raise RuntimeError("Install MeshShield with the 'crypto' extra to use Ed25519") from exc
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_bytes, public_bytes


def sign_payload(payload: dict[str, Any], private_key: bytes) -> str:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        signature = Ed25519PrivateKey.from_private_bytes(private_key).sign(
            canonical_payload(payload)
        )
    except ImportError as exc:
        raise RuntimeError("Install MeshShield with the 'crypto' extra to use Ed25519") from exc
    return base64.b64encode(signature).decode("ascii")


def verify_payload(payload: dict[str, Any], signature: str, public_key: bytes) -> bool:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(public_key).verify(
            base64.b64decode(signature, validate=True), canonical_payload(payload)
        )
        return True
    except ImportError as exc:
        raise RuntimeError("Install MeshShield with the 'crypto' extra to use Ed25519") from exc
    except (ValueError, InvalidSignature):
        return False
