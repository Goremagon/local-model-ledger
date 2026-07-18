# Local Model Ledger

Open evidence for running AI locally.

Local Model Ledger is a provider-neutral, machine-readable catalog for answering two different
questions without pretending they are the same:

1. Can an exact model artifact run on a given hardware and runtime configuration?
2. How well did that artifact perform on a stated task and benchmark?

The project is an evidence ledger, not a universal ranking and not a model downloader. Every claim
must retain its artifact identity, source, method, confidence, freshness, and redistribution status.

## Status

The repository has published its first bounded source snapshot. It contains 107 pinned ModelFit
staging candidates, two exact artifacts resolved through a maintainer-controlled local Ollama API,
and four production records: two runtime-verified artifact records and two conservative fit
estimates. It does not claim comprehensive coverage.

## Design principles

- Exact artifacts matter: revision, format, quantization, runtime, backend, and context are part of
  identity.
- Measured results remain separate from estimates.
- Hardware performance remains separate from task quality.
- Missing evidence stays unknown; it is never converted into a favorable score.
- Every field that came from elsewhere retains field-level provenance.
- Records without confirmed redistribution rights cannot enter public release snapshots.
- Automated collectors propose changes; validation and review publish them.
- Consumers make their own policy decisions. The ledger supplies evidence, not execution authority.

## Planned public interface

Stable releases will be immutable JSONL snapshots under `catalog/releases/`, accompanied by a
manifest and SHA-256 checksum. Consumers may pin a release, validate it locally, and apply their own
hardware and task policies without sending machine details to this project.

## Repository layout

```text
catalog/          Rights-cleared source records and generated release snapshots
docs/             Methodology, governance, and build plan
schema/           Versioned JSON Schema contracts
scripts/          Deterministic validation and release tooling
sources/          Allowlisted-source definitions and licensing review notes
tests/            Validator and contract tests
```

## Quick validation

```bash
python -m pip install -e .[dev]
python -m scripts.validate_catalog
python -m scripts.validate_staging
python -m pytest
```

To reproduce the current collection and release from the reviewed inputs:

```bash
python -m scripts.collect_modelfit
python -m scripts.resolve_ollama_local
python -m scripts.promote_candidates
python -m scripts.build_snapshot --version 0.1.0 --released-at 2026-07-18T21:00:00Z
```

The resolver queries only a local Ollama API and requires an exact tag match. It does not scrape or
automate Ollama-hosted services. Promotion is limited to candidate IDs explicitly listed in
`reviews/approvals.json`.

## Relationship to Lattice

Local Model Ledger is independent public infrastructure. Obsidian Lattice is expected to be its
first opt-in consumer through a provider-neutral catalog adapter, but the data contract is intended
for any application.

## Licensing

- Repository tooling and documentation are MIT licensed; see `LICENSE`.
- Original, rights-cleared catalog data is intended for CC0 release; see `DATA_LICENSE.md`.
- A source license never automatically becomes the license of normalized data. Every imported or
  contributed record must pass the provenance and redistribution review described in
  `docs/GOVERNANCE.md`.

## Contributing

See `CONTRIBUTING.md`. During bootstrap, contributions should focus on the schema, methodology,
source reviews, and reproducible sample measurements rather than bulk imports.
