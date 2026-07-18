from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schema" / "catalog-record.schema.json"
DEFAULT_RECORDS = ROOT / "catalog" / "records"


def iter_records(records_dir: Path):
    for path in sorted(records_dir.rglob("*.json")):
        yield path, json.loads(path.read_text(encoding="utf-8"))
    for path in sorted(records_dir.rglob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                yield Path(f"{path}:{line_number}"), json.loads(line)


def validate_catalog(schema_path: Path, records_dir: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}

    for source, record in iter_records(records_dir):
        for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "<root>"
            errors.append(f"{source}: {location}: {error.message}")
        record_id = record.get("record_id")
        if isinstance(record_id, str):
            if record_id in seen_ids:
                errors.append(f"{source}: duplicate record_id {record_id!r}; first seen in {seen_ids[record_id]}")
            else:
                seen_ids[record_id] = source

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Local Model Ledger source records")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    args = parser.parse_args()

    errors = validate_catalog(args.schema, args.records)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    count = sum(1 for _ in iter_records(args.records))
    print(f"Validated {count} catalog record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
