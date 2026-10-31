# Contributing

MeshShield is a small research simulator. Contributions are welcome if they keep
three properties: the core stays standard-library only, every claim is measured,
and nothing pretends to be a real payment system.

## Setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

Coverage has a floor of 80% (`pyproject.toml`). CI runs the suite on Python 3.11
and 3.12 on Ubuntu and Windows, then builds the site and Docker image.

## What we look for

- **Tests for every claim.** A feature that says it is causal needs a test that
  adds a future row and asserts the past does not change.
- **Determinism.** No `datetime.now()`, no unseeded `random`, no wall-clock in the
  pipeline. If a process needs randomness, take a seed.
- **Honest copy.** If a number changes, update the README, the site data and the
  docs in the same pull request. Never hand-edit a metric that a run can produce.
- **Separated evidence.** Integrity findings and model contributions stay in
  different fields and different UI sections.
- **Small dependencies.** Runtime deps stay in the extras (`crypto`, `graph`,
  `boost`, `docs`, `data`). The CLI must work without any of them.

## Commits

Use a short conventional prefix and explain the why:

```
feat(features): add causal two-hop features
fix(sync): reject duplicate event IDs before scoring
docs(eval): refresh holdout numbers after the seed change
```

Keep unrelated changes out of the same commit. Do not rewrite published history.

## Refreshing the published numbers

```powershell
$env:PYTHONPATH = "src"
python -m meshshield.cli demo
python scripts/export_site_data.py
python -m pytest -q
```

Then update the measured tables in `README.md` and `docs/evaluation.md` from the
new `data/generated/metrics.json`, and commit the regenerated
`site/src/data/results.js`. If a claim no longer holds, remove it; do not soften
it into something unfalsifiable.

## Reporting a bug

Open an issue with the command, the seed, the profile, and the full traceback.
For security issues, follow [SECURITY.md](SECURITY.md) instead of opening a
public issue.
