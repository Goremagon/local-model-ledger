# Contributing

Local Model Ledger welcomes schema, tooling, methodology, source-review, and reproducible evidence
contributions.

## Before submitting data

Do not submit copied leaderboard rows or scraped databases merely because they are publicly visible.
Confirm that the record can be redistributed and record the applicable terms. If rights are unclear,
open a source-review issue instead of a data pull request.

Measurements must identify the exact artifact, runtime version, backend, context, hardware, method,
and relevant settings. Remove serial numbers, usernames, hostnames, IP addresses, and other personal
or machine-identifying data.

## Pull-request checks

```bash
python -m pip install -e .[dev]
ruff check .
python -m scripts.validate_catalog
python -m pytest
```

Automated source collectors must open reviewable pull requests. They must not push directly to
`main` or silently change published snapshots.
