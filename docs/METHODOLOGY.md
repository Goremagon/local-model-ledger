# Methodology

## Evidence dimensions

Local Model Ledger keeps these dimensions independent:

1. Artifact metadata: exact identity, revision, format, precision, size, context, and license.
2. Fit evidence: whether an artifact can load under stated capacity and headroom assumptions.
3. Hardware performance: memory, load time, prompt throughput, generation throughput, and latency.
4. Task quality: named benchmark, benchmark version, settings, and metric.

No dimension silently fills another. A task score cannot prove machine fit; a successful load cannot
prove task quality; an estimate cannot be presented as a measurement.

## Evidence grades

- `exact_measured`: reproduced on the stated artifact/runtime/hardware configuration.
- `runtime_verified`: the runtime successfully loaded or preflighted the exact artifact.
- `conservative_estimate`: attributable metadata and disclosed bounded calculations.
- `reported`: a permitted external claim not independently reproduced here.

## Identity and joins

Joins require the exact artifact revision and precision. Performance joins additionally require the
runtime, backend, context, and material flags. Family-name inheritance is prohibited in release
records unless represented as a clearly labelled estimate with a documented derivation.

## Hardware privacy

Community submissions must use the minimum hardware description needed for comparison. Serial
numbers, hostnames, account names, IP addresses, and stable device identifiers are prohibited.

## Corrections

Published releases are immutable. Corrections supersede records in a new release and identify the
superseded record and reason. Consumers can therefore reproduce an older decision while receiving a
clear upgrade path.
