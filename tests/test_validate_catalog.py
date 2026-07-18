from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_catalog import DEFAULT_SCHEMA, validate_catalog


def valid_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "record_id": "fixture:model:q4:measurement:1",
        "record_kind": "hardware_measurement",
        "artifact": {
            "source": "fixture",
            "identifier": "example/model",
            "revision": "0123456789abcdef",
            "format": "GGUF",
            "precision": "Q4_K_M",
        },
        "runtime": {
            "name": "fixture-runtime",
            "version": "1.0.0",
            "backend": "cpu",
            "context_tokens": 2048,
        },
        "hardware": {
            "os": "fixture-os",
            "cpu": "fixture-cpu",
            "ram_bytes": 17179869184,
            "accelerators": [],
        },
        "evidence": {
            "grade": "exact_measured",
            "method": "fixture only; not catalog data",
            "metrics": {"generation_tokens_per_second": 1.0},
        },
        "provenance": {
            "source_url": "https://example.invalid/fixture",
            "retrieved_at": "2026-07-18T00:00:00Z",
            "contributor": "test fixture",
            "data_license": "CC0-1.0",
            "redistribution_verified": True,
        },
        "review": {
            "status": "approved_for_snapshot",
            "reviewed_at": "2026-07-18T00:00:00Z",
            "expires_at": "2027-07-18T00:00:00Z",
            "reviewer": "test fixture",
        },
    }


def write_record(directory: Path, record: dict, name: str = "record.json") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(record), encoding="utf-8")


def test_valid_record_passes(tmp_path: Path) -> None:
    write_record(tmp_path, valid_record())
    assert validate_catalog(DEFAULT_SCHEMA, tmp_path) == []


def test_unverified_redistribution_fails(tmp_path: Path) -> None:
    record = valid_record()
    record["provenance"]["redistribution_verified"] = False
    write_record(tmp_path, record)
    assert any("True was expected" in error for error in validate_catalog(DEFAULT_SCHEMA, tmp_path))


def test_duplicate_ids_fail(tmp_path: Path) -> None:
    record = valid_record()
    write_record(tmp_path, record, "one.json")
    write_record(tmp_path, record, "two.json")
    assert any("duplicate record_id" in error for error in validate_catalog(DEFAULT_SCHEMA, tmp_path))
