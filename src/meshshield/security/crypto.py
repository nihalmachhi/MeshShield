"""Signing, key rotation and revocation for sync payloads.

Two signers are provided:

* :class:`SimulatedSigner` uses an HMAC-SHA256 with a per-device secret. It is the
  default so a bare standard-library install can still demonstrate the whole
  integrity path. It is **not** a substitute for public-key signatures: anyone
  holding the shared secret can forge.
* :class:`Ed25519Signer` uses the optional ``cryptography`` dependency and signs
  with a real private key. Enable it with ``pip install "meshshield[crypto]"``.

Canonical bytes
---------------
A payload is signed over ``json.dumps(payload, sort_keys=True,
separators=(",", ":"), ensure_ascii=False)`` encoded as UTF-8. That exact string
is what :func:`canonical_payload` returns, and the threat-model tests assert that
reordering keys or adding whitespace changes the digest.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from meshshield.core.domain import parse_timestamp

SIGNED_FIELDS: tuple[str, ...] = (
    "event_id",
    "transaction_id",
    "device_id",
    "account_id",
    "merchant_id",
    "amount",
    "currency",
    "event_time",
    "device_counter",
)


def canonical_payload(payload: dict[str, Any]) -> bytes:
    """Serialize a payload to the exact bytes that get signed."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def payload_digest(payload: dict[str, Any]) -> str:
    """Return the SHA-256 digest of the canonical bytes."""
    return hashlib.sha256(canonical_payload(payload)).hexdigest()


def signable(tx: Any) -> dict[str, Any]:
    """Extract the signed field set from a transaction-like object."""
    return {name: getattr(tx, name) for name in SIGNED_FIELDS}


def tamper_bytes(signature: str) -> str:
    """Flip one character of a signature to simulate corruption."""
    if not signature:
        return "0" * 64
    first = "1" if signature[0] != "1" else "2"
    return first + signature[1:]


class Signer(Protocol):
    """Minimal signer contract used by the generator and the verifier."""

    key_id: str

    def sign(self, payload: dict[str, Any]) -> str: ...

    def verify(self, payload: dict[str, Any], signature: str) -> bool: ...


@dataclass(frozen=True)
class SimulatedSigner:
    """Deterministic HMAC signer for a standard-library-only demo."""

    key_id: str
    secret: bytes

    @classmethod
    def for_device(cls, device_id: str, key_id: str | None = None) -> SimulatedSigner:
        """Derive a stable secret from the device ID (demo only, not a real key)."""
        return cls(
            key_id=key_id or f"{device_id}-sim-1",
            secret=hashlib.sha256(f"meshshield-demo-key:{device_id}".encode()).digest(),
        )

    def sign(self, payload: dict[str, Any]) -> str:
        return hmac.new(self.secret, canonical_payload(payload), hashlib.sha256).hexdigest()

    def verify(self, payload: dict[str, Any], signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)


@dataclass(frozen=True)
class Ed25519Signer:
    """Real Ed25519 signer. Requires the ``crypto`` extra."""

    key_id: str
    private_key: bytes
    public_key: bytes

    @classmethod
    def generate(cls, key_id: str) -> Ed25519Signer:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
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
        return cls(key_id=key_id, private_key=private_bytes, public_key=public_bytes)

    def sign(self, payload: dict[str, Any]) -> str:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError("Install MeshShield with the 'crypto' extra to use Ed25519") from exc
        signature = Ed25519PrivateKey.from_private_bytes(self.private_key).sign(
            canonical_payload(payload)
        )
        return base64.b64encode(signature).decode("ascii")

    def verify(self, payload: dict[str, Any], signature: str) -> bool:
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError("Install MeshShield with the 'crypto' extra to use Ed25519") from exc
        try:
            Ed25519PublicKey.from_public_bytes(self.public_key).verify(
                base64.b64decode(signature, validate=True), canonical_payload(payload)
            )
        except (InvalidSignature, ValueError):
            return False
        return True


class KeyStatus(StrEnum):
    VALID = "valid"
    NOT_YET_VALID = "not_yet_valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class KeyRecord:
    """One registered key, with the window in which its signatures are trusted."""

    key_id: str
    verifier: Signer
    valid_from: datetime
    valid_to: datetime | None = None
    revoked_at: datetime | None = None
    device_id: str = ""

    def status(self, at: datetime) -> KeyStatus:
        moment = at.astimezone(UTC)
        if moment < self.valid_from:
            return KeyStatus.NOT_YET_VALID
        if self.revoked_at is not None and moment >= self.revoked_at:
            return KeyStatus.REVOKED
        if self.valid_to is not None and moment >= self.valid_to:
            return KeyStatus.EXPIRED
        return KeyStatus.VALID


class KeyRegistry:
    """Registry of device keys supporting rotation and revocation."""

    def __init__(self) -> None:
        self._records: dict[str, KeyRecord] = {}

    def register(
        self,
        verifier: Signer,
        valid_from: datetime | str,
        valid_to: datetime | str | None = None,
        revoked_at: datetime | str | None = None,
        device_id: str = "",
    ) -> KeyRecord:
        record = KeyRecord(
            key_id=verifier.key_id,
            verifier=verifier,
            valid_from=_as_datetime(valid_from),
            valid_to=_as_datetime(valid_to) if valid_to is not None else None,
            revoked_at=_as_datetime(revoked_at) if revoked_at is not None else None,
            device_id=device_id,
        )
        self._records[record.key_id] = record
        return record

    def get(self, key_id: str) -> KeyRecord | None:
        return self._records.get(key_id)

    def status(self, key_id: str, at: datetime | str) -> KeyStatus:
        record = self._records.get(key_id)
        if record is None:
            return KeyStatus.UNKNOWN
        return record.status(_as_datetime(at))

    def verify(self, key_id: str, payload: dict[str, Any], signature: str) -> bool:
        record = self._records.get(key_id)
        if record is None:
            return False
        return record.verifier.verify(payload, signature)

    def revoke(self, key_id: str, at: datetime | str) -> None:
        record = self._records[key_id]
        self._records[key_id] = KeyRecord(
            key_id=record.key_id,
            verifier=record.verifier,
            valid_from=record.valid_from,
            valid_to=record.valid_to,
            revoked_at=_as_datetime(at),
            device_id=record.device_id,
        )

    def rotate(self, old_key_id: str, new_verifier: Signer, at: datetime | str) -> KeyRecord:
        """Close the old key's window and register its replacement at the same instant."""
        moment = _as_datetime(at)
        record = self._records[old_key_id]
        self._records[old_key_id] = KeyRecord(
            key_id=record.key_id,
            verifier=record.verifier,
            valid_from=record.valid_from,
            valid_to=moment,
            revoked_at=record.revoked_at,
            device_id=record.device_id,
        )
        return self.register(new_verifier, valid_from=moment, device_id=record.device_id)


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(UTC)


def new_device_secret() -> bytes:
    """Return a fresh random secret for a simulated device key."""
    return secrets.token_bytes(32)


def parse_timestamp_safe(value: str) -> datetime:
    """Re-export the contract parser so callers do not import two helpers."""
    return parse_timestamp(value)
