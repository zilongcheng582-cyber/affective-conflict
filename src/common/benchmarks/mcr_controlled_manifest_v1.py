#!/usr/bin/env python3
"""Build and validate the immutable 909 x 3 controlled-arbitration manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ARMS = ("A_ONLY", "T_ONLY", "A_T")
PROTOCOL_VERSION = "mcr_controlled_arbitration_v1"
ONTOLOGY_VERSION = "mcr_ser_ontology_v1"
PARSER_VERSION = "mcr_ser_parser_v1"
PROMPT_VERSION = "mcr_controlled_arbitration_prompt_v1"
EXECUTION_CONFIG_VERSION = "qwen25_mcr_controlled_execution_v1"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_manifests(text_evidence_path: Path, manifest_path: Path, gate_path: Path) -> dict[str, Any]:
    evidence = load_jsonl(text_evidence_path)
    if len(evidence) != 909:
        raise ValueError(f"expected 909 evidence rows, observed {len(evidence)}")
    rows: list[dict[str, Any]] = []
    seen_samples = set()
    for item in sorted(evidence, key=lambda row: (int(row["source_index"]), row["sample_id"])):
        sample_id = item["sample_id"]
        source_index = int(item["source_index"])
        if sample_id in seen_samples:
            raise ValueError(f"duplicate sample_id: {sample_id}")
        seen_samples.add(sample_id)
        for arm in ARMS:
            rows.append(
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "record_key": f"{sample_id}::{arm}",
                    "sample_id": sample_id,
                    "source_index": source_index,
                    "arm": arm,
                    "audio": item["audio"] if arm in ("A_ONLY", "A_T") else None,
                    "text_evidence": item["text_evidence"] if arm in ("T_ONLY", "A_T") else None,
                    "y_audio": item["y_audio"],
                    "y_text": item["y_text"],
                    "ontology_version": ONTOLOGY_VERSION,
                    "parser_version": PARSER_VERSION,
                    "prompt_version": PROMPT_VERSION,
                    "execution_config_version": EXECUTION_CONFIG_VERSION,
                }
            )
    if len(rows) != 2727:
        raise ValueError(f"expected 2727 manifest rows, observed {len(rows)}")
    by_sample: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_sample.setdefault(row["sample_id"], []).append(row)
    if len(by_sample) != 909 or any(len(group) != 3 for group in by_sample.values()):
        raise ValueError("three-arm grouping failure")
    if any(row["y_audio"] == row["y_text"] for row in rows):
        raise ValueError("y_audio/y_text conflict invariant failed")
    for sample_id, group in by_sample.items():
        arms = {row["arm"] for row in group}
        if arms != set(ARMS):
            raise ValueError(f"arm set failure for {sample_id}: {arms}")
        a_only = next(row for row in group if row["arm"] == "A_ONLY")
        t_only = next(row for row in group if row["arm"] == "T_ONLY")
        a_t = next(row for row in group if row["arm"] == "A_T")
        if a_only["audio"] != a_t["audio"] or t_only["text_evidence"] != a_t["text_evidence"]:
            raise ValueError(f"cross-arm evidence mismatch for {sample_id}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    gate_rows = [row for row in rows if int(row["source_index"]) in (0, 1)]
    if len(gate_rows) != 6:
        raise ValueError(f"expected 6 gate rows, observed {len(gate_rows)}")
    with gate_path.open("w", encoding="utf-8") as handle:
        for row in gate_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "PASS",
        "records": len(rows),
        "samples": len(by_sample),
        "arm_counts": {arm: sum(row["arm"] == arm for row in rows) for arm in ARMS},
        "gate_records": len(gate_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-evidence", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_manifests(args.text_evidence, args.manifest, args.gate), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
