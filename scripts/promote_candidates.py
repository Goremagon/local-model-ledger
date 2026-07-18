from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from scripts.pipeline_common import ROOT, read_json, read_jsonl, slug, write_json


def artifact_block(candidate: dict[str, Any]) -> dict[str, Any]:
    artifact = candidate["resolution"]["artifact"]
    return {
        "source": "ollama",
        "identifier": artifact["identifier"],
        "revision": f"sha256:{artifact['revision']}",
        "format": artifact["format"],
        "precision": artifact["precision"],
        "size_bytes": artifact["size_bytes"],
        "parameter_count": artifact["parameter_count"],
        "native_context_tokens": artifact["native_context_tokens"],
        "model_license": artifact["model_license"],
    }


def review_block(approval: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "approved_for_snapshot",
        "reviewed_at": approval["reviewed_at"],
        "expires_at": approval["expires_at"],
        "reviewer": approval["reviewer"],
    }


def promote(candidate: dict[str, Any], approval: dict[str, Any]) -> list[dict[str, Any]]:
    resolution = candidate["resolution"]
    artifact = resolution["artifact"]
    if not artifact.get("model_license") or artifact["model_license"] == "LicenseRef-Unclassified-Text":
        raise ValueError(f"{candidate['candidate_id']}: model license is missing or unclassified")
    digest_prefix = artifact["revision"][:16]
    identifier_slug = slug(artifact["identifier"])
    common = {
        "schema_version": "1.0.0",
        "artifact": artifact_block(candidate),
        "review": review_block(approval),
    }
    metadata = {
        **common,
        "record_id": f"artifact:{identifier_slug}:{digest_prefix}",
        "record_kind": "artifact_metadata",
        "evidence": {
            "grade": "runtime_verified",
            "method": "Exact installed artifact returned by the maintainer-controlled local Ollama API.",
            "metrics": {
                "locally_installed": True,
                "capabilities": ",".join(artifact.get("capabilities", [])),
                "license_text_sha256": artifact.get("license_text_sha256"),
            },
            "notes": ["No model weights or license text are redistributed by this record."],
        },
        "provenance": {
            "source_url": "https://github.com/ollama/ollama/blob/main/docs/api.md",
            "source_revision": artifact["revision"],
            "retrieved_at": resolution["resolved_at"],
            "contributor": approval["reviewer"],
            "data_license": "CC0-1.0",
            "redistribution_verified": True,
            "required_attribution": None,
        },
    }
    advisory = candidate["advisory"]
    fit = {
        **common,
        "record_id": f"fit:{identifier_slug}:{digest_prefix}:modelfit",
        "record_kind": "fit_estimate",
        "evidence": {
            "grade": "conservative_estimate",
            "method": "ModelFit pinned dataset estimate joined to an exact local Ollama tag and digest.",
            "metrics": {
                "minimum_ram_bytes": advisory["minimum_ram_bytes"],
                "estimated_load_bytes": advisory["estimated_load_bytes"],
                "task_tags": ",".join(advisory["task_tags"]),
                "runs_locally": advisory["runs_locally"],
                "open_weights_reported": advisory["open_weights"],
            },
            "notes": [
                "Memory values are estimates, not measurements.",
                "ModelFit attribution and methodology are preserved in provenance.",
            ],
        },
        "provenance": {
            "source_url": candidate["source"]["source_url"],
            "source_revision": candidate["source"]["source_revision"],
            "retrieved_at": resolution["resolved_at"],
            "contributor": "ModelFit; normalized by Local Model Ledger",
            "data_license": candidate["source"]["data_license"],
            "redistribution_verified": True,
            "required_attribution": candidate["source"]["required_attribution"],
        },
    }
    return [metadata, fit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote explicitly approved resolved candidates")
    parser.add_argument("--input", type=Path, default=ROOT / "staging" / "resolved" / "ollama-local.jsonl")
    parser.add_argument("--approvals", type=Path, default=ROOT / "reviews" / "approvals.json")
    parser.add_argument("--output", type=Path, default=ROOT / "catalog" / "records" / "generated")
    args = parser.parse_args()

    candidates = {item["candidate_id"]: item for item in read_jsonl(args.input)}
    approvals = read_json(args.approvals)
    records: list[dict[str, Any]] = []
    for approval in approvals["approvals"]:
        candidate_id = approval["candidate_id"]
        if candidate_id not in candidates:
            raise ValueError(f"approved candidate is not resolved: {candidate_id}")
        records.extend(promote(candidates[candidate_id], approval))

    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    for record in sorted(records, key=lambda item: item["record_id"]):
        write_json(args.output / f"{record['record_id'].replace(':', '__')}.json", record)
    print(f"Promoted {len(approvals['approvals'])} candidates into {len(records)} records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
