# Local Model Ledger build plan

## Objective

Build a public, provider-neutral, automatically maintainable evidence catalog that applications can
use to advise which local AI model artifacts fit particular hardware and tasks without overpromising
coverage or accuracy.

## Non-goals

- A universal "best model" ranking.
- Automatic model download or execution.
- Uploading consumer hardware profiles by default.
- Treating estimated speed as measured performance.
- Republishing visible data without confirmed rights.
- Exhaustively testing every model on every machine.

## LML0 — contracts and governance

Deliver the v1 record schema, evidence grades, source-admission checklist, contribution rules,
validator, tests, and CI. Keep the production catalog empty until the first source passes review.

Exit criteria:

- valid records pass locally and in CI;
- duplicate IDs and unverified redistribution fail;
- hardware measurements require runtime and hardware identity;
- task evaluations require benchmark identity;
- documentation clearly separates code and data licensing.

## LML1 — first external advisory snapshot

Perform a formal source review of the ModelFit hardware compatibility dataset. If its CC BY 4.0
scope, attribution, endpoint stability, and field semantics pass review, implement a pinned importer
that preserves attribution and marks estimates as estimates. Generate a proposed snapshot through a
pull request; do not fetch live data at consumer runtime.

Exit criteria:

- importer is deterministic for a pinned upstream revision;
- every normalized field has recorded provenance;
- attribution is included in the release manifest;
- no estimated field is labelled measured;
- a source outage leaves the last release reproducible.

## LML2 — artifact metadata collectors

Add allowlisted collectors for exact Hugging Face and Ollama artifacts after separate terms reviews.
Normalize revisions, formats, precision, sizes, context metadata, runtime identifiers, model
licenses, and gated status. Collectors create pull requests on a schedule.

Exit criteria:

- aliases never replace exact revisions in evidence records;
- missing or conflicting licenses block public promotion;
- stale and deleted upstream artifacts are surfaced, not silently erased;
- collector changes cannot rewrite prior releases.

## LML3 — measured hardware evidence

Define a privacy-minimized submission envelope and reproducible harness for load success, peak
RAM/VRAM, time to first token, prompt throughput, and generation throughput. Evaluate LocalScore
interoperability only after public database/API rights are confirmed. Accept direct community
submissions through reviewed pull requests.

Exit criteria:

- exact runtime, backend, context, flags, and artifact are captured;
- repeated samples and aggregation rules are disclosed;
- personal hardware identifiers are rejected;
- outliers are retained with flags rather than silently averaged away.

## LML4 — task-quality evidence

Add separately licensed task-evaluation sources or project-run reproducible evaluations. Preserve
benchmark version, prompt/template settings, evaluation harness, metric definitions, and known
contamination limitations. Keep task results independent of hardware performance.

Exit criteria:

- task categories map to named benchmark evidence;
- inherited or self-reported scores are explicitly graded;
- upstream benchmark terms permit the released representation;
- no composite score hides missing evidence.

## LML5 — immutable releases and consumer SDK

Generate sorted JSONL snapshots, a manifest, schema version, source versions, attribution bundle,
record counts, detached checksum, and supersession map. Publish through GitHub Releases and provide a
small reference client that pins, downloads, verifies, and queries a snapshot locally.

Exit criteria:

- identical reviewed inputs produce byte-identical snapshots;
- consumers can operate fully offline after download;
- release verification fails closed on checksum/schema errors;
- the previous release remains available and usable.

## LML6 — public browser and sustainable automation

Generate a static GitHub Pages browser for artifacts, hardware measurements, tasks, sources,
confidence, and freshness. Add scheduled collector PRs, source-health reports, correction queues,
and contributor documentation without requiring an always-on paid service.

Exit criteria:

- pages are generated from signed release data, not a hidden database;
- users can distinguish measurement, estimate, and missing evidence;
- automation never merges or publishes data autonomously;
- source suspension and record quarantine are documented and tested.

## Initial implementation order

1. Complete LML0 and publish the bootstrap repository.
2. Build a Lattice adapter against a pinned fixture of the schema.
3. Review ModelFit as the first optional bridge source.
4. Publish the first rights-cleared advisory snapshot.
5. Use consumer feedback to revise the schema before adding broad collectors.

This order proves that somebody can consume the contract before the project invests in an expensive
generalized ingestion system.
