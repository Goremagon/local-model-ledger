from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [canonical_json(value) for value in values]
    path.write_bytes(("\n".join(lines) + ("\n" if lines else "")).encode("utf-8"))


def validate_records(schema_path: Path, values: Iterable[dict[str, Any]]) -> list[str]:
    validator = Draft202012Validator(read_json(schema_path), format_checker=FormatChecker())
    errors: list[str] = []
    for index, value in enumerate(values):
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "<root>"
            errors.append(f"record {index}: {location}: {error.message}")
    return errors


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:80] or "unnamed"


def parse_parameter_count(label: str | None) -> int | None:
    if not label:
        return None
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([bm])\s*", label.lower())
    if not match:
        return None
    multiplier = 1_000_000_000 if match.group(2) == "b" else 1_000_000
    return round(float(match.group(1)) * multiplier)


def detect_model_license(license_text: str | None) -> tuple[str | None, str | None]:
    if not license_text or not license_text.strip():
        return None, None
    digest = sha256_bytes(license_text.encode("utf-8"))
    normalized = " ".join(license_text.lower().split())
    if "apache license" in normalized and "version 2.0" in normalized:
        return "Apache-2.0", digest
    if "mit license" in normalized and "permission is hereby granted" in normalized:
        return "MIT", digest
    if "llama 3.2 community license agreement" in normalized:
        return "LicenseRef-Llama-3.2-Community", digest
    if "llama 3.1 community license agreement" in normalized:
        return "LicenseRef-Llama-3.1-Community", digest
    if "gemma terms of use" in normalized:
        return "LicenseRef-Gemma-Terms", digest
    return "LicenseRef-Unclassified-Text", digest
