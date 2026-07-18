# Local Model Ledger

Open evidence for running AI locally.

Local Model Ledger is a provider-neutral, machine-readable catalog for answering two different
questions without pretending they are the same:

1. Can an exact model artifact run on a given hardware and runtime configuration?
2. How well did that artifact perform on a stated task and benchmark?

The project is an evidence ledger, not a universal ranking and not a model downloader. Every claim
must retain its artifact identity, source, method, confidence, freshness, and redistribution status.

## Status

The repository is in its contract-first bootstrap stage. It currently contains the schema,
validation tooling, contribution rules, methodology, governance, and staged build plan. It does not
yet publish production catalog records or claim comprehensive coverage.

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
python scripts/validate_catalog.py
python -m pytest
```

An empty catalog is valid during bootstrap. Production releases will not be created until at least
one rights-cleared source record and its provenance pass review.

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
