# Repository setup checklist

Copy-paste metadata for the GitHub **About** panel and repository settings.
Nothing here is applied automatically; it is a checklist for the maintainer.

## About description

```text
Offline payment risk research simulator: point-in-time features, signature and replay checks, explainable synthetic scores, and a chronological holdout evaluation.
```

## Topics

Paste these one at a time in **Settings → General → Topics**, or use the
comma-separated list in the API/CLI:

```text
fraud-detection, offline-payments, synthetic-data, machine-learning, python,
graph-features, idempotency, event-time, point-in-time-features,
streaming-data, risk-scoring, anomaly-detection, reproducibility
```

Comma-separated, for `gh repo edit`:

```bash
gh repo edit nihalmachhi/MeshShield \
  --description "Offline payment risk research simulator: point-in-time features, signature and replay checks, explainable synthetic scores, and a chronological holdout evaluation." \
  --add-topic fraud-detection \
  --add-topic offline-payments \
  --add-topic synthetic-data \
  --add-topic machine-learning \
  --add-topic python \
  --add-topic graph-features \
  --add-topic idempotency \
  --add-topic event-time \
  --add-topic point-in-time-features \
  --add-topic reproducibility
```

## Repository settings

| Setting | Value | Why |
| --- | --- | --- |
| Description | see above | One line, no hype. |
| Website | `https://nihalmachhi.github.io/MeshShield/` | The Pages deployment. |
| Topics | see above | Discoverability. |
| Default branch | `main` | Matches both workflows. |
| Pages source | **GitHub Actions** | `site.yml` publishes `site/dist`. |
| Actions permissions | Read repository contents | Least privilege for CI. |
| Secret scanning | On | Free for public repos. |
| Dependabot alerts | On | Tracks the few optional dependencies. |
| Social preview | `docs/assets/social-preview.png` once captured | 1280×640. |

## Pages configuration

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. Push to `main`; `.github/workflows/site.yml` builds `site/` and deploys `site/dist`.
3. The workflow sets `VITE_BASE_PATH=/MeshShield/` automatically for project sites.
   For a user/organisation site (`<user>.github.io`) set it to `/`.

## Branch protection (recommended)

- Require the `quality` and `site` checks to pass before merging.
- Require linear history; the commit log is part of the story of this project.
- Do not squash — every task in `docs/CHANGES.md` points at a commit.

## Badges

The README already uses:

```markdown
![CI](https://github.com/nihalmachhi/MeshShield/actions/workflows/ci.yml/badge.svg)
![Site](https://github.com/nihalmachhi/MeshShield/actions/workflows/site.yml/badge.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
```

They only render correctly once the repository is public and the workflows have
run at least once.
