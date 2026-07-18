from __future__ import annotations

import argparse
import json
import shlex
import urllib.request
from pathlib import Path
from typing import Any

from scripts.pipeline_common import (
    ROOT,
    canonical_json,
    read_json,
    sha256_bytes,
    slug,
    validate_records,
    write_jsonl,
)


SOURCE_CONFIG = ROOT / "sources" / "modelfit-hardware-dataset.json"
CANDIDATE_SCHEMA = ROOT / "schema" / "candidate-record.schema.json"


def parse_ollama_ref(command: Any) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return None
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if len(parts) == 3 and parts[0].lower() == "ollama" and parts[1].lower() == "run":
        return parts[2]
    return None


def gib_to_bytes(value: Any) -> int | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    return round(float(value) * 1024**3)


def transform_model(row: dict[str, Any], index: int, config: dict[str, Any]) -> dict[str, Any]:
    row_hash = sha256_bytes(canonical_json(row).encode("utf-8"))[:12]
    name = str(row.get("model") or f"row-{index}")
    params = row.get("params")
    parameter_count = round(float(params) * 1_000_000_000) if isinstance(params, (int, float)) else None
    task_tags = [part.strip().lower() for part in str(row.get("bestFor") or "").split(",") if part.strip()]
    runtimes = [str(item).strip().lower() for item in row.get("runtimes", []) if str(item).strip()]
    kv_kb = row.get("kvKbPerToken")
    return {
        "schema_version": "1.0.0",
        "candidate_id": f"modelfit:{slug(name)}:{row_hash}",
        "state": "metadata_valid",
        "source": {
            "source_id": config["source_id"],
            "source_url": config["source_url"],
            "source_revision": config["source_revision"],
            "row_index": index,
            "data_license": config["data_license"],
            "required_attribution": config["required_attribution"],
        },
        "artifact_hint": {
            "display_name": name,
            "family": str(row.get("family") or "unknown"),
            "ollama_ref": parse_ollama_ref(row.get("ollamaCommand")),
            "format": "GGUF" if "llama.cpp" in runtimes or "ollama" in runtimes else "unknown",
            "precision": str(row.get("quantization") or "unknown"),
            "parameter_count": parameter_count,
        },
        "advisory": {
            "minimum_ram_bytes": gib_to_bytes(row.get("minRamGb")),
            "estimated_load_bytes": gib_to_bytes(row.get("estimatedLoadGb")),
            "runtimes": runtimes,
            "task_tags": sorted(set(task_tags)),
            "runs_locally": bool(row.get("runsLocally")),
            "open_weights": bool(row.get("openWeights")),
            "gguf_diy": bool(row.get("ggufDiy")),
            "kv_bytes_per_token": round(float(kv_kb) * 1024) if isinstance(kv_kb, (int, float)) else None,
        },
    }


def collect(source_bytes: bytes, config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actual_hash = sha256_bytes(source_bytes)
    if actual_hash != config["expected_sha256"]:
        raise ValueError(f"source SHA-256 mismatch: expected {config['expected_sha256']}, got {actual_hash}")
    dataset = json.loads(source_bytes)
    if dataset.get("attribution") != config["source_attribution"]:
        raise ValueError("dataset attribution changed from the reviewed source attribution")
    candidates = [transform_model(row, index, config) for index, row in enumerate(dataset["models"])]
    candidates.sort(key=lambda item: item["candidate_id"])
    errors = validate_records(CANDIDATE_SCHEMA, candidates)
    if errors:
        raise ValueError("candidate validation failed:\n" + "\n".join(errors))
    return dataset, candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect the pinned ModelFit dataset into staging")
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--config", type=Path, default=SOURCE_CONFIG)
    parser.add_argument("--output-root", type=Path, default=ROOT / "staging")
    args = parser.parse_args()

    config = read_json(args.config)
    source_bytes = (
        args.source_file.read_bytes()
        if args.source_file
        else urllib.request.urlopen(config["source_url"], timeout=30).read()
    )
    dataset, candidates = collect(source_bytes, config)
    raw_dir = args.output_root / "raw" / config["source_id"] / config["source_revision"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "models.json").write_bytes(source_bytes)
    write_jsonl(args.output_root / "candidates" / "modelfit.jsonl", candidates)
    print(f"Collected {len(dataset['models'])} rows into {len(candidates)} validated candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
