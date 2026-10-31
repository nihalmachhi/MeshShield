# Security policy

MeshShield is a local research simulator. It does not move money, store real
payment data or expose a network service by default.

## Supported versions

The `main` branch and the latest tagged release receive fixes. Older snapshots
are not maintained.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability. Use GitHub's private
vulnerability reporting on the repository (Security → Report a vulnerability),
or contact the maintainer listed in `pyproject.toml`. Include:

- the affected version or commit,
- a minimal reproduction,
- the impact you believe it has.

You should get an acknowledgement within a week. This is a volunteer project, so
there is no paid bounty and no formal SLA.

## What is in scope

- The simulated signature scheme: a valid signature must not verify after the
  signed payload or key identifier changes.
- The integrity gate: duplicate IDs, replayed events, revoked keys and impossible
  event times must be reported, not silently accepted.
- The local API: path traversal against the static file handler, JSON injection or
  unbounded request handling.
- The dependency surface: a core install must not import optional packages.

## What is out of scope

- **The simulator is not a payment system.** Authorizing or settling real money is
  explicitly out of scope.
- **Do not expose the API.** `serve` binds to `127.0.0.1` and has no
  authentication, authorization, TLS or rate limiting. A public deployment is a
  misconfiguration, not a supported mode.
- **Simulated cryptography.** `SimulatedSigner` uses a keyed hash for
  reproducibility. It is not a real signature scheme, and the files under
  `data/generated/` are not secrets. Use the `crypto` extra and `Ed25519Signer`
  if you need real signatures in an experiment.
- **Synthetic labels.** A finding or a high score is not evidence of fraud.

## Hardening checklist for local use

- Keep `serve` on loopback; pass `--host 127.0.0.1` explicitly.
- Do not commit `data/generated/`, keys or `.env` files; they are git-ignored.
- Keep optional extras current if you install them.
- Treat downloaded public datasets under their own licence and access rules. The
  repository does not redistribute them.
