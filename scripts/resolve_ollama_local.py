from __future__ import annotations

import argparse
import copy
import ipaddress
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.pipeline_common import (
    ROOT,
    detect_model_license,
    parse_parameter_count,
    read_jsonl,
    validate_records,
    write_json,
    write_jsonl,
)


CANDIDATE_SCHEMA = ROOT / "schema" / "candidate-record.schema.json"


def require_loopback(endpoint: str) -> None:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("endpoint must be an HTTP(S) URL")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError as error:
        if parsed.hostname != "localhost":
            raise ValueError("resolver endpoint must be loopback or localhost") from error
    else:
        if not address.is_loopback:
            raise ValueError("resolver endpoint must be loopback or localhost")


def request_json(endpoint: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        endpoint.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def first_context_length(model_info: dict[str, Any]) -> int | None:
    values = [
        value
        for key, value in model_info.items()
        if key.endswith(".context_length") and isinstance(value, int) and value > 0
    ]
    return min(values) if values else None


def resolve_candidates(
    candidates: list[dict[str, Any]],
    tags_response: dict[str, Any],
    show_responses: dict[str, dict[str, Any]],
    runtime_version: str,
    resolved_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    installed: dict[str, dict[str, Any]] = {}
    for model in tags_response.get("models", []):
        for key in {str(model.get("name", "")).lower(), str(model.get("model", "")).lower()}:
            if key:
                installed[key] = model

    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    for candidate in candidates:
        reference = candidate["artifact_hint"].get("ollama_ref")
        model = installed.get(str(reference).lower()) if reference else None
        if not model:
            unresolved.append({"candidate_id": candidate["candidate_id"], "reason": "no_exact_local_tag_match"})
            continue
        show = show_responses.get(str(reference).lower(), {})
        details = model.get("details") or show.get("details") or {}
        parameter_count = parse_parameter_count(details.get("parameter_size"))
        context_tokens = first_context_length(show.get("model_info") or {})
        license_id, license_hash = detect_model_license(show.get("license"))
        if not parameter_count or not context_tokens:
            unresolved.append({"candidate_id": candidate["candidate_id"], "reason": "incomplete_local_metadata"})
            continue
        item = copy.deepcopy(candidate)
        item["state"] = "resolved"
        item["resolution"] = {
            "artifact": {
                "source": "ollama-local",
                "identifier": str(model.get("model") or model.get("name")),
                "revision": str(model["digest"]),
                "format": str(details.get("format") or candidate["artifact_hint"]["format"]),
                "precision": str(details.get("quantization_level") or candidate["artifact_hint"]["precision"]),
                "size_bytes": int(model["size"]),
                "parameter_count": parameter_count,
                "native_context_tokens": context_tokens,
                "model_license": license_id,
                "license_text_sha256": license_hash,
                "capabilities": sorted(str(value) for value in show.get("capabilities", [])),
            },
            "runtime": {
                "name": "ollama",
                "version": runtime_version,
                "backend": "local-auto",
            },
            "resolved_at": resolved_at,
            "resolver": "ollama-local-api-exact-match-v1",
        }
        resolved.append(item)

    resolved.sort(key=lambda item: item["candidate_id"])
    report = {
        "resolver": "ollama-local-api-exact-match-v1",
        "runtime_version": runtime_version,
        "resolved_at": resolved_at,
        "candidate_count": len(candidates),
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "unresolved": sorted(unresolved, key=lambda item: item["candidate_id"]),
    }
    return resolved, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve staging candidates against local Ollama")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--input", type=Path, default=ROOT / "staging" / "candidates" / "modelfit.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "staging" / "resolved" / "ollama-local.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "staging" / "reports" / "ollama-local.json")
    parser.add_argument("--resolved-at")
    args = parser.parse_args()

    require_loopback(args.endpoint)
    candidates = read_jsonl(args.input)
    tags = request_json(args.endpoint, "/api/tags")
    version = str(request_json(args.endpoint, "/api/version").get("version") or "unknown")
    installed_names = {
        str(model.get("name") or model.get("model"))
        for model in tags.get("models", [])
        if model.get("name") or model.get("model")
    }
    shows = {
        name.lower(): request_json(args.endpoint, "/api/show", {"model": name, "verbose": False})
        for name in installed_names
    }
    resolved_at = args.resolved_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    resolved, report = resolve_candidates(candidates, tags, shows, version, resolved_at)
    errors = validate_records(CANDIDATE_SCHEMA, resolved)
    if errors:
        raise ValueError("resolved candidate validation failed:\n" + "\n".join(errors))
    write_jsonl(args.output, resolved)
    write_json(args.report, report)
    print(f"Resolved {len(resolved)} of {len(candidates)} candidates by exact local tag match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
