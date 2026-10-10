# Threat model and safe-use notes

## Assets and trust assumptions

The current assets are local synthetic records, generated model parameters, and a SQLite idempotency database. The user controls the machine and the synthetic generator. There are no external accounts, credentials, real payment rails, or production data integrations.

## Simulated threats

- Duplicate delivery of the same event ID.
- Replayed event identifiers and duplicate transaction identifiers in the integrity layer.
- Invalid signature outcomes represented by a Boolean simulation field.
- Late and out-of-order synchronization.
- Shared-device relationships, high amounts, and bursts as synthetic risk patterns.

These are demonstrations, not cryptographic verification. No signing keys or signatures are implemented. A Boolean `signature_valid` value is trusted input from the simulator.

## Application boundary

The local HTTP service has no authentication, authorization, TLS, CSRF protection, or rate limiting. It binds to `127.0.0.1` by default. Do not bind it to a public or shared network. If the prototype is ever extended to handle authorized data, add access control, encryption, retention limits, audit controls, privacy review, and secure key management before integration.

## Model and data risks

Synthetic rules can make a score appear stronger than it is. Labels can be noisy in real use; the current labels are scenario definitions. Device sharing can have legitimate explanations. False positives can cause harm. A model contribution only describes an association in this fitted model, not intent or causality. Do not use scores to block transactions, freeze accounts, or accuse a person.
