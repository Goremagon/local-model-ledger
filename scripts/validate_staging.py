from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.pipeline_common import ROOT, read_json, read_jsonl, sha256_bytes, validate_records


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    config = read_json(ROOT / "sources" / "modelfit-hardware-dataset.json")
    raw_path = (
        ROOT
        / "staging"
        / "raw"
        / config["source_id"]
        / config["source_revision"]
        / "models.json"
    )
    if not raw_path.exists():
        errors.append(f"missing pinned raw source: {raw_path}")
    elif sha256_bytes(raw_path.read_bytes()) != config["expected_sha256"]:
        errors.append("pinned ModelFit source hash does not match its reviewed source config")

    schema = ROOT / "schema" / "candidate-record.schema.json"
    candidates = read_jsonl(ROOT / "staging" / "candidates" / "modelfit.jsonl")
    resolved = read_jsonl(ROOT / "staging" / "resolved" / "ollama-local.jsonl")
    errors.extend(f"candidate: {error}" for error in validate_records(schema, candidates))
    errors.extend(f"resolved: {error}" for error in validate_records(schema, resolved))
    candidate_ids = [item["candidate_id"] for item in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("staging candidate IDs are not unique")
    resolved_ids = {item["candidate_id"] for item in resolved}
    if not resolved_ids.issubset(set(candidate_ids)):
        errors.append("resolved staging records contain unknown candidate IDs")

    report = read_json(ROOT / "staging" / "reports" / "ollama-local.json")
    if report["candidate_count"] != len(candidates) or report["resolved_count"] != len(resolved):
        errors.append("resolver report counts do not match committed staging files")
    approvals = read_json(ROOT / "reviews" / "approvals.json")["approvals"]
    approved_ids = [item["candidate_id"] for item in approvals]
    if len(approved_ids) != len(set(approved_ids)):
        errors.append("approval candidate IDs are not unique")
    missing_approvals = sorted(set(approved_ids) - resolved_ids)
    if missing_approvals:
        errors.append(f"approvals reference unresolved candidates: {', '.join(missing_approvals)}")

    release_root = ROOT / "catalog" / "releases"
    for release_dir in sorted(path for path in release_root.glob("v*") if path.is_dir()):
        manifest_path = release_dir / "manifest.json"
        catalog_path = release_dir / "catalog.jsonl"
        checksums_path = release_dir / "SHA256SUMS"
        if not all(path.exists() for path in (manifest_path, catalog_path, checksums_path)):
            errors.append(f"{release_dir.name}: release files are incomplete")
            continue
        manifest = read_json(manifest_path)
        release_records = read_jsonl(catalog_path)
        if manifest["record_count"] != len(release_records):
            errors.append(f"{release_dir.name}: manifest record count is incorrect")
        for filename, metadata in manifest["files"].items():
            target = release_dir / filename
            if not target.exists() or file_sha256(target) != metadata["sha256"]:
                errors.append(f"{release_dir.name}: manifest hash mismatch for {filename}")
        for line in checksums_path.read_text(encoding="utf-8").splitlines():
            expected, filename = line.split("  ", 1)
            target = release_dir / filename
            if not target.exists() or file_sha256(target) != expected:
                errors.append(f"{release_dir.name}: SHA256SUMS mismatch for {filename}")

    if errors:
        raise ValueError("staging/release validation failed:\n" + "\n".join(errors))
    print(
        f"Validated {len(candidates)} candidates, {len(resolved)} resolutions, "
        f"{len(approvals)} approvals, and committed releases."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
