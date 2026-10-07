#!/usr/bin/env python3
"""Deterministically strip the verified MCR adversarial wrapper."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


EXTRACTOR_VERSION = "mcr_controlled_text_extractor_v1"
DESCRIPTION_MARKER = "Description:"
CLASSIFICATION_INSTRUCTION = (
    "Classify this emotion into one of the following categories: sad, happy, fearful, "
    "angry, surprised, disgusted, or neutral."
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def extract_adversarial_description(source_field: str) -> str:
    """Return only the source Description content, preserving no wrapper text."""

    marker_start = source_field.find(DESCRIPTION_MARKER)
    if marker_start < 0:
        raise ValueError("missing Description: marker")
    description_end = marker_start + len(DESCRIPTION_MARKER)
    instruction_start = source_field.find(CLASSIFICATION_INSTRUCTION, description_end)
    if instruction_start < 0:
        raise ValueError("missing exact classification instruction")
    raw_segment = source_field[description_end:instruction_start]
    evidence = raw_segment.strip()
    if not evidence:
        raise ValueError("empty extracted Description content")
    leading = raw_segment[: len(raw_segment) - len(raw_segment.lstrip())]
    trailing = raw_segment[len(raw_segment.rstrip()) :]
    round_trip = (
        source_field[:description_end]
        + leading
        + evidence
        + trailing
        + source_field[instruction_start:]
    )
    if round_trip != source_field:
        raise ValueError("exact structural round-trip failed")
    if "The following text provides descriptions derived from audio content." in evidence:
        raise ValueError("source reliability wrapper leaked into evidence")
    if CLASSIFICATION_INSTRUCTION in evidence:
        raise ValueError("classification instruction leaked into evidence")
    return evidence


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_text_evidence_artifact(
    pool_path: Path,
    source_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    with pool_path.open("r", encoding="utf-8", newline="") as handle:
        pool = list(csv.DictReader(handle))
    if len(pool) != 909:
        raise ValueError(f"expected 909 authoritative pool records, observed {len(pool)}")
    rows: list[dict[str, Any]] = []
    seen = set()
    for pool_row in pool:
        index = int(pool_row["original_record_index"])
        source_row = source[index]
        if source_row.get("audio") != pool_row["audio"] or source_row.get("gt") != pool_row["gt"]:
            raise ValueError(f"source identity mismatch at source_index={index}")
        if source_row.get("adversarial") != pool_row["adversarial"]:
            raise ValueError(f"source adversarial field mismatch at source_index={index}")
        text_evidence = extract_adversarial_description(source_row["adversarial"])
        repeat = extract_adversarial_description(source_row["adversarial"])
        if text_evidence != repeat:
            raise ValueError(f"non-deterministic extraction at source_index={index}")
        key = (pool_row["sample_id"], index, pool_row["audio"])
        if key in seen:
            raise ValueError(f"duplicate controlled sample identity: {key}")
        seen.add(key)
        rows.append(
            {
                "sample_id": pool_row["sample_id"],
                "source_index": index,
                "audio": pool_row["audio"],
                "y_audio": pool_row["gt"],
                "y_text": pool_row["competitor_emotion"],
                "text_evidence": text_evidence,
                "source_adversarial_field_sha256": sha256_bytes(
                    source_row["adversarial"].encode("utf-8")
                ),
                "extractor_version": EXTRACTOR_VERSION,
            }
        )
    rows.sort(key=lambda row: (row["source_index"], row["sample_id"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "PASS",
        "extractor_version": EXTRACTOR_VERSION,
        "records": len(rows),
        "nonempty": sum(bool(row["text_evidence"]) for row in rows),
        "pool_sha256": _sha256_file(pool_path),
        "source_sha256": _sha256_file(source_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_text_evidence_artifact(args.pool, args.source, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
