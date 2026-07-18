from __future__ import annotations

import json

import pytest

from scripts.collect_modelfit import collect
from scripts.pipeline_common import detect_model_license
from scripts.promote_candidates import promote
from scripts.resolve_ollama_local import require_loopback, resolve_candidates


def source_config(source_bytes: bytes) -> dict:
    from scripts.pipeline_common import sha256_bytes

    return {
        "source_id": "fixture",
        "source_url": "https://example.invalid/models.json",
        "source_revision": "fixture-revision",
        "expected_sha256": sha256_bytes(source_bytes),
        "data_license": "CC-BY-4.0",
        "source_attribution": "Fixture: https://example.invalid/",
        "required_attribution": "Fixture: https://example.invalid/",
    }


def dataset_bytes() -> bytes:
    return json.dumps(
        {
            "attribution": "Fixture: https://example.invalid/",
            "models": [
                {
                    "model": "Example 7B",
                    "family": "Example",
                    "params": 7,
                    "quantization": "Q4_K_M",
                    "minRamGb": 10,
                    "estimatedLoadGb": 5.5,
                    "runtimes": ["ollama", "llama.cpp"],
                    "bestFor": "Coding, Chat",
                    "runsLocally": True,
                    "openWeights": True,
                    "ggufDiy": False,
                    "ollamaCommand": "ollama run example:7b",
                }
            ],
        }
    ).encode()


def test_collect_creates_untrusted_candidate() -> None:
    source = dataset_bytes()
    _, candidates = collect(source, source_config(source))
    assert candidates[0]["state"] == "metadata_valid"
    assert candidates[0]["artifact_hint"]["ollama_ref"] == "example:7b"
    assert candidates[0]["advisory"]["estimated_load_bytes"] == round(5.5 * 1024**3)


def test_collect_rejects_changed_source_bytes() -> None:
    source = dataset_bytes()
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        collect(source + b" ", source_config(source))


def test_exact_local_match_resolves() -> None:
    source = dataset_bytes()
    _, candidates = collect(source, source_config(source))
    tags = {
        "models": [
            {
                "name": "example:7b",
                "model": "example:7b",
                "size": 4_000_000_000,
                "digest": "a" * 64,
                "details": {"format": "gguf", "parameter_size": "7B", "quantization_level": "Q4_K_M"},
            }
        ]
    }
    shows = {
        "example:7b": {
            "details": tags["models"][0]["details"],
            "model_info": {"example.context_length": 8192},
            "capabilities": ["completion"],
            "license": "Apache License\nVersion 2.0, January 2004",
        }
    }
    resolved, report = resolve_candidates(candidates, tags, shows, "1.0.0", "2026-07-18T00:00:00Z")
    assert report["resolved_count"] == 1
    assert resolved[0]["resolution"]["artifact"]["revision"] == "a" * 64
    assert resolved[0]["resolution"]["artifact"]["native_context_tokens"] == 8192


def test_non_loopback_resolver_is_rejected() -> None:
    with pytest.raises(ValueError, match="loopback"):
        require_loopback("https://ollama.com")


def test_license_detection_is_bounded() -> None:
    assert detect_model_license("Apache License\nVersion 2.0, January 2004")[0] == "Apache-2.0"
    assert detect_model_license("Some custom terms")[0] == "LicenseRef-Unclassified-Text"


def test_promotion_rejects_unclassified_model_license() -> None:
    candidate = {"candidate_id": "fixture:candidate", "resolution": {"artifact": {"model_license": "LicenseRef-Unclassified-Text"}}}
    with pytest.raises(ValueError, match="missing or unclassified"):
        promote(candidate, {})
