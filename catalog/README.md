# Catalog

`records/` contains reviewed source records. `releases/` will contain generated immutable JSONL
snapshots, manifests, and checksums.

No production data is published during bootstrap. Test fixtures belong under `tests/` and must never
be included in a release snapshot.
