from __future__ import annotations

import argparse
import hashlib
import shutil
from collections import Counter
from pathlib import Path

from scripts.pipeline_common import ROOT, canonical_json, write_json
from scripts.validate_catalog import iter_records, validate_catalog


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an immutable catalog release snapshot")
    parser.add_argument("--version", required=True)
    parser.add_argument("--released-at", required=True)
    parser.add_argument("--records", type=Path, default=ROOT / "catalog" / "records")
    parser.add_argument("--output-root", type=Path, default=ROOT / "catalog" / "releases")
    args = parser.parse_args()

    errors = validate_catalog(ROOT / "schema" / "catalog-record.schema.json", args.records)
    if errors:
        raise ValueError("catalog validation failed:\n" + "\n".join(errors))
    records = sorted((record for _, record in iter_records(args.records)), key=lambda item: item["record_id"])
    release_dir = args.output_root / f"v{args.version}"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    catalog_path = release_dir / "catalog.jsonl"
    catalog_path.write_bytes(
        ("\n".join(canonical_json(record) for record in records) + "\n").encode("utf-8")
    )
    attributions = sorted(
        {
            record["provenance"]["required_attribution"]
            for record in records
            if record["provenance"].get("required_attribution")
        }
    )
    attribution_path = release_dir / "ATTRIBUTION.md"
    attribution_path.write_bytes(
        ("# Attribution\n\n" + "\n".join(f"- {item}" for item in attributions) + "\n").encode(
            "utf-8"
        )
    )
    manifest = {
        "catalog": "Local Model Ledger",
        "catalog_schema_version": "1.0.0",
        "release": args.version,
        "released_at": args.released_at,
        "record_count": len(records),
        "record_kinds": dict(sorted(Counter(record["record_kind"] for record in records).items())),
        "data_licenses": dict(sorted(Counter(record["provenance"]["data_license"] for record in records).items())),
        "files": {
            "catalog.jsonl": {"sha256": digest(catalog_path)},
            "ATTRIBUTION.md": {"sha256": digest(attribution_path)},
        },
    }
    manifest_path = release_dir / "manifest.json"
    write_json(manifest_path, manifest)
    checksums = [
        f"{digest(attribution_path)}  ATTRIBUTION.md",
        f"{digest(catalog_path)}  catalog.jsonl",
        f"{digest(manifest_path)}  manifest.json",
    ]
    (release_dir / "SHA256SUMS").write_bytes(("\n".join(checksums) + "\n").encode("utf-8"))
    print(f"Built v{args.version} with {len(records)} records at {release_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
