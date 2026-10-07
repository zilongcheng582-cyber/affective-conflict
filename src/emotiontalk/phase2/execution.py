from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate


import argparse

import csv

import hashlib

import importlib.metadata as metadata

import importlib.util

import json

import math

import os

import random

import re

import statistics

import sys

import time

import traceback

from collections import Counter, defaultdict

from datetime import datetime, timezone

from pathlib import Path

ROOT = project_root()

AUDIT = ROOT / "audit/EMOTIONTALK_CONTROLLED_V1"

PHASE1 = AUDIT / "phase1_competence_full_v1_2"

PLAN = PHASE1 / "EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json"

SAMPLE = PHASE1 / "EMOTIONTALK_PHASE1_SAMPLE_TABLE_V1_2.csv"

V1_GATE = AUDIT / "phase2_pairwise_gate_v1"

V1_GATE_REPORT = V1_GATE / "EMOTIONTALK_PHASE2_PAIRWISE_GATE_V1.json"

V1_GATE_PROV = V1_GATE / "EMOTIONTALK_PHASE2_PAIRWISE_GATE_V1_PROVENANCE.json"

V1_GATE_SELECTION = V1_GATE / "EMOTIONTALK_PHASE2_PAIRWISE_GATE_SELECTION_V1.csv"

V1_GATE_JSONL = V1_GATE / "emotiontalk_phase2_pairwise_gate_v1.jsonl"

V1_AMENDMENT = V1_GATE / "EMOTIONTALK_PHASE2_PAIRWISE_GATE_V1_PROVENANCE_AMENDMENT_001.json"

GATE = AUDIT / "phase2_pairwise_gate_v1_2"

FULL = AUDIT / "phase2_pairwise_full_v1_attempt_002"

LEGACY_FULL = AUDIT / "phase2_pairwise_full_v1"

RUNNER = ROOT / "code/run_qwen25_emotiontalk_pairwise_v1_2.py"

POPULATION_SHA = "0363b012bf5ce083854efa210d2b739c04a10262136ba6abc81e3d7438d05e20"

from src.emotiontalk.phase2 import core as base
ONTOLOGY = tuple(base.ONTOLOGY)

PAIR_MODALITIES = {"AT": ("A", "T"), "AV": ("A", "V"), "VT": ("V", "T")}

PAIR_ARMS = {"AT": ("A_THEN_T", "T_THEN_A"),
             "AV": ("A_THEN_V", "V_THEN_A"),
             "VT": ("V_THEN_T", "T_THEN_V")}

MODALITY_LABEL_FIELDS = {"A": "audio_emotion", "T": "text_emotion", "V": "video_emotion"}

EXPECTED_COUNTS = {
    "AT": {"total": 397, "conflict": 62, "consistent": 335},
    "AV": {"total": 371, "conflict": 146, "consistent": 225},
    "VT": {"total": 298, "conflict": 140, "consistent": 158},
}

EXPECTED_GENERATIONS = {"AT": 794, "AV": 742, "VT": 596}

FULL_JSONL = FULL / "emotiontalk_phase2_pairwise_full_v1_attempt_002.jsonl"

def now():
    return datetime.now(timezone.utc).isoformat()

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def dump_json(path, obj):
    Path(path).write_text(json.dumps(base.jsonable(obj), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def population_and_plan(phase1=None):
    if phase1 is None:
        phase1 = base.read_json(base.PHASE1_JSON)
    plan = base.read_json(PLAN)
    if sha256(PLAN) != POPULATION_SHA:
        raise RuntimeError(f"population plan SHA mismatch: {sha256(PLAN)}")
    counts, eligible, memberships, _, summary = base.population_preflight(phase1)
    if counts != EXPECTED_COUNTS or memberships != 1066:
        raise RuntimeError(f"Phase 1 sample-table population mismatch: {counts}")
    if plan.get("planned_phase2_joint_generations") != 2132:
        raise RuntimeError("population plan total is not 2132")
    for pair, expected in EXPECTED_COUNTS.items():
        p = plan.get("pairs", {}).get(pair, {})
        actual = {"total": p.get("dual_readable_total"),
                  "conflict": p.get("conflict_and_dual_readable_N"),
                  "consistent": p.get("consistent_and_dual_readable_N"),
                  "planned": p.get("planned_joint_generations")}
        if actual != {**expected, "planned": EXPECTED_GENERATIONS[pair]}:
            raise RuntimeError(f"population plan {pair} counts mismatch: {actual}")
        strata = {"conflict": set(p.get("conflict_utterance_ids", [])),
                  "consistent": set(p.get("consistent_utterance_ids", []))}
        table_ids = {s: {r["utterance_id"] for r, st in eligible[pair] if st == s}
                     for s in ("conflict", "consistent")}
        if strata != table_ids:
            raise RuntimeError(f"population plan {pair} IDs do not match sample table")
    return phase1, plan, counts, eligible

def current_frozen_hashes():
    out = {}
    for name, (path, expected) in base.EXPECTED_HASHES.items():
        actual = sha256(path)
        out[name] = {"path": str(path), "expected": expected, "actual": actual, "pass": actual == expected}
    out["phase2_population_plan"] = {"path": str(PLAN), "expected": POPULATION_SHA,
                                    "actual": sha256(PLAN), "pass": sha256(PLAN) == POPULATION_SHA}
    return out

def generation_config():
    return {"model": "Qwen2.5-Omni-7B", "model_path": str(ROOT / "models/Qwen2.5-Omni-7B"),
            "dtype": "torch.bfloat16", "device_map": "cuda", "attention_implementation": "flash_attention_2",
            "processor": "Qwen2_5OmniProcessor", "processor_local_files_only": True,
            "generation": {"do_sample": False, "max_new_tokens": 16,
                           "use_audio_in_video": False, "return_audio": False},
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "1")}

def hash_for(hashes, *tokens):
    tokens = tuple(t.lower() for t in tokens)
    for name, value in hashes.items():
        haystack = (str(name) + " " + str(value.get("path", ""))).lower()
        if all(token in haystack for token in tokens):
            return value.get("actual")
    return None

def selection_signature(row):
    fields = ("utterance_id", "pair", "stratum", "arm", "evidence_1_modality",
              "evidence_1_reference", "evidence_2_modality", "evidence_2_reference",
              "instruction_position", "candidate_sequence_id", "candidate_sequence",
              "audio_path", "text_path", "silent_video_path")
    return tuple(str(row.get(k, "")) for k in fields)

def prepare_full_rows(eligible, plan):
    panel = {r["utterance_id"]: r for r in base.read_csv(base.PANEL_CSV)}
    media = {r["utterance_id"]: r for r in base.read_csv(base.MEDIA_CSV)}
    candidates = {r["candidate_sequence_id"]: r["pipe"] for r in base.read_json(base.CANDIDATE_PATH)["sequences"]}
    resources = {}
    for r in base.read_csv(base.RESOURCE_CSV):
        try:
            resources[r["utterance_id"]] = float(r.get("resource_proxy_duration_width_height") or 0)
        except ValueError:
            resources[r["utterance_id"]] = 0.0
    all_ids = sorted({r["utterance_id"] for pair in eligible.values() for r, _ in pair})
    text_paths = base.text_index(all_ids)
    text_cache = {}
    for uid, path in text_paths.items():
        try:
            text = base.read_json(path).get("content")
            text_cache[uid] = (text, path, None) if isinstance(text, str) else (None, path, "official Text.content is not a string")
        except Exception as e:
            text_cache[uid] = (None, path, repr(e))
    result = []
    for pair in ("AT", "AV", "VT"):
        entries = sorted(eligible[pair], key=lambda x: x[0]["utterance_id"])
        rank_map = {}
        if pair in ("AV", "VT"):
            ranked = sorted((r["utterance_id"] for r, _ in entries),
                            key=lambda uid: (-resources.get(uid, 0.0), uid))
            rank_map = {uid: i + 1 for i, uid in enumerate(ranked)}
        for r, stratum in entries:
            uid = r["utterance_id"]
            p, m = panel[uid], media[uid]
            pair_m1, pair_m2 = PAIR_MODALITIES[pair]
            y1 = p[MODALITY_LABEL_FIELDS[pair_m1]]
            y2 = p[MODALITY_LABEL_FIELDS[pair_m2]]
            if (y1 != y2) != (stratum == "conflict"):
                raise RuntimeError(f"source relation mismatch for {uid}/{pair}")
            if (p["candidate_sequence_id"] != r["candidate_sequence_id"]
                    or p["candidate_sequence"] != r["candidate_sequence"]
                    or candidates.get(p["candidate_sequence_id"]) != p["candidate_sequence"]):
                raise RuntimeError(f"frozen candidate sequence mismatch for {uid}/{pair}")
            labels = p["candidate_sequence"].split("|")
            if len(labels) != 7 or len(set(labels)) != 7 or set(labels) != set(ONTOLOGY):
                raise RuntimeError(f"invalid candidate sequence for {uid}/{pair}")
            if p["audio_path"] != m["audio_path"] or p["video_path"] != m["source_av_video_path"]:
                raise RuntimeError(f"panel/media reference mismatch for {uid}/{pair}")
            text, text_path, text_error = text_cache[uid]
            if text is not None and text != p["text"]:
                text_error = "official Text.content differs from frozen master panel"
            audio_path = base.resolve_media(p["audio_path"])
            video_path = base.resolve_media(m["silent_video_path"])
            if m.get("validation_status") != "PASS" or str(m.get("silent_audio_stream_count")) != "0":
                text_error = text_error or "media manifest does not certify silent video"
            sample = {"utterance_id": uid, "candidate_sequence_id": p["candidate_sequence_id"],
                      "candidate_sequence": p["candidate_sequence"], "candidate_labels": labels,
                      "text": text, "text_json_path": str(text_path), "text_path": str(text_path),
                      "audio_path": str(audio_path), "silent_video_path": str(video_path),
                      "video_duration": m.get("duration"), "resource_proxy": resources.get(uid, 0.0),
                      "resource_rank_within_pair": rank_map.get(uid), "video_preflight_error": text_error,
                      "y_M1": y1, "y_M2": y2,
                      "labels_by_modality": {pair_m1: y1, pair_m2: y2},
                      "speaker_id": p.get("speaker_id"), "official_split": p.get("official_split"),
                      "trimodal_pattern": p.get("trimodal_pattern")}
            for arm in PAIR_ARMS[pair]:
                first, second = base.ORDER[arm]
                refs = {"A": str(audio_path), "T": str(text_path), "V": str(video_path)}
                result.append({"utterance_id": uid, "pair": pair, "stratum": stratum, "arm": arm,
                               "evidence_1_modality": first, "evidence_1_reference": refs[first],
                               "evidence_2_modality": second, "evidence_2_reference": refs[second],
                               "instruction_position": "AFTER_EVIDENCE_2",
                               "candidate_sequence_id": p["candidate_sequence_id"],
                               "candidate_sequence": p["candidate_sequence"], "candidate_labels": labels,
                               "y_M1": y1, "y_M2": y2, "source_relation": "CONFLICT" if stratum == "conflict" else "CONSISTENT",
                               "audio_path": str(audio_path), "text_path": str(text_path),
                               "silent_video_path": str(video_path), "video_duration": m.get("duration"),
                               "resource_proxy": resources.get(uid, 0.0), "resource_rank_within_pair": rank_map.get(uid),
                               "sample": sample})
    expected_keys = {(r["utterance_id"], pair, arm) for pair, entries in eligible.items()
                     for r, _ in entries for arm in PAIR_ARMS[pair]}
    actual_keys = [(r["utterance_id"], r["pair"], r["arm"]) for r in result]
    if len(result) != 2132 or len(set(actual_keys)) != 2132 or set(actual_keys) != expected_keys:
        raise RuntimeError(f"full row primary-key/population mismatch: rows={len(result)}, unique={len(set(actual_keys))}")
    return result

def canonical_outcomes(record, parsed_label):
    if parsed_label not in ONTOLOGY:
        return "PARSE_FAIL", "PARSE_FAIL"
    if record["source_relation"] == "CONSISTENT":
        return ("SHARED_LABEL" if parsed_label == record["y_M1"] else "OTHER", "SHARED_LABEL" if parsed_label == record["y_M1"] else "OTHER")
    if parsed_label == record["y_M1"]:
        modality = PAIR_MODALITIES[record["pair"]][0]
        return "SIDE_MODALITY_1", f"SIDE_{modality}"
    if parsed_label == record["y_M2"]:
        modality = PAIR_MODALITIES[record["pair"]][1]
        return "SIDE_MODALITY_2", f"SIDE_{modality}"
    return "OTHER", "OTHER"

def normalize_template_result(value):
    """Phase 1 V1.2 frozen contract: str or exactly one str in a list."""
    if isinstance(value, str):
        return value, "str"
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value[0], "singleton_list_str"
    raise TypeError(f"chat template must return str or singleton list[str], got {type(value).__name__}")

def execute_pairwise_record(rec, index, processor, model, torch, process_mm_info, parse_label, prompt_cfg):
    """The sole Gate/full record executor. Keep this exact function for both modes."""
    first_mod, second_mod = base.ORDER[rec["arm"]]
    sample = rec["sample"]
    out = {k: v for k, v in rec.items() if k not in ("sample", "candidate_labels")}
    out.update({
        "record_index": index,
        "primary_key": {"utterance_id": rec["utterance_id"], "pair": rec["pair"], "arm": rec["arm"]},
        "source_relation": rec["source_relation"],
        "y_first": sample["labels_by_modality"][first_mod],
        "y_second": sample["labels_by_modality"][second_mod],
        "input_evidence_references": [rec["evidence_1_reference"], rec["evidence_2_reference"]],
        "actual_evidence_order": [first_mod, second_mod],
        "generation_attempted": False, "generation_success": False,
        "parser_execution": False, "parser_executed": False, "parser_status": None,
        "parsed_label": None, "joint_outcome": None, "canonical_modality_outcome": None,
        "raw_generation": None, "runtime_seconds": None,
        "failure_type": None, "failure_message": None, "traceback": None,
        "video_sampled_frame_metadata": None, "video_stream_count": None, "audio_stream_count": None,
        "gpu_before": None, "gpu_after": None,
    })
    start = time.monotonic()
    stage = "INPUT_CONSTRUCTION"
    try:
        if sample.get("video_preflight_error"):
            raise RuntimeError(sample["video_preflight_error"])
        for path in (Path(rec["audio_path"]), Path(rec["text_path"])):
            if not path.is_file() or path.stat().st_size <= 0:
                raise FileNotFoundError(f"required evidence missing or empty: {path}")
        if "V" in (first_mod, second_mod):
            vpath = Path(rec["silent_video_path"])
            if not vpath.is_file() or vpath.stat().st_size <= 0:
                raise FileNotFoundError(f"silent video missing or empty: {vpath}")
            probe = base.probe_streams(vpath)
            out["silent_video_stream_probe"] = probe
            out["video_stream_count"] = probe.get("video_stream_count")
            out["audio_stream_count"] = probe.get("audio_stream_count")
            if probe["video_stream_count"] < 1 or probe["audio_stream_count"] != 0:
                raise RuntimeError(f"silent-video stream contract failed: {probe}")
        out["gpu_before"] = base.gpu_snapshot(torch)
        messages = base.build_messages(rec, prompt_cfg)
        stage = "CHAT_TEMPLATE"
        rendered_raw = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        rendered, rendered_type = normalize_template_result(rendered_raw)
        out["chat_template_return_type"] = rendered_type
        stage = "MEDIA_DECODE"
        audios, images, videos = process_mm_info(messages, use_audio_in_video=False)
        stage = "PROCESSOR"
        inputs = processor(text=rendered, audio=audios, images=images, videos=videos,
                           return_tensors="pt", padding=True, use_audio_in_video=False)
        if "V" in (first_mod, second_mod):
            out["video_sampled_frame_metadata"] = base.tensor_metadata(videos, inputs)
            out["video_sampled_frame_metadata"]["source_duration_seconds"] = rec["video_duration"]
            out["video_sampled_frame_metadata"]["resource_rank_within_pair"] = rec["resource_rank_within_pair"]
        inputs = inputs.to(model.device).to(model.dtype)
        stage = "GENERATION"
        torch.cuda.reset_peak_memory_stats()
        out["generation_attempted"] = True
        generated = model.generate(**inputs, do_sample=False, max_new_tokens=16,
                                   use_audio_in_video=False, return_audio=False)
        torch.cuda.synchronize()
        stage = "OUTPUT_DECODE"
        trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, generated)]
        decoded = processor.batch_decode(trimmed, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=False)
        if not isinstance(decoded, list) or len(decoded) != 1 or not isinstance(decoded[0], str):
            raise TypeError("batch_decode must return singleton list[str]")
        out["raw_generation"] = decoded[0]
        out["generation_success"] = True
        out["gpu_after"] = base.gpu_snapshot(torch)
        stage = "PARSER"
        parsed = parse_label(out["raw_generation"])
        out["parser_execution"] = True
        out["parser_executed"] = True
        out["parser_status"] = parsed.get("parser_status") if isinstance(parsed, dict) else "PARSER_EXCEPTION"
        out["parsed_label"] = parsed.get("parsed_label") if isinstance(parsed, dict) else None
        out["parser_result"] = parsed
        out["joint_outcome"], out["canonical_modality_outcome"] = canonical_outcomes(out, out["parsed_label"])
        if out["parser_status"] == "PARSE_FAIL":
            out["failure_type"] = "PARSE_FAIL"
            out["failure_message"] = "frozen parser did not recognize one exact ontology label"
        stage = "COMPLETE"
    except Exception as e:
        out["failure_message"] = repr(e)
        out["traceback"] = traceback.format_exc()
        msg = (repr(e) + " " + out["traceback"]).lower()
        fatal = isinstance(e, (AttributeError, NameError, AssertionError, KeyError)) or stage == "CHAT_TEMPLATE"
        out["fatal_runner_implementation_failure"] = bool(fatal)
        if fatal:
            out["failure_type"] = "FATAL_RUNNER_IMPLEMENTATION_FAILURE"
        elif stage in ("INPUT_CONSTRUCTION", "MEDIA_DECODE"):
            out["failure_type"] = "MEDIA_FAILURE"
        elif stage == "PROCESSOR":
            out["failure_type"] = "PROCESSOR_FAILURE"
        elif stage == "GENERATION" and ("out of memory" in msg or "cuda error: out of memory" in msg):
            out["failure_type"] = "CUDA_OOM"
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
        elif stage in ("GENERATION", "OUTPUT_DECODE"):
            out["failure_type"] = "GENERATION_FAILURE"
        elif stage == "PARSER":
            out["failure_type"] = "PARSER_EXCEPTION"
        else:
            out["failure_type"] = "UNKNOWN_TECHNICAL_FAILURE"
        if out["generation_success"] and not out["parser_execution"]:
            out["joint_outcome"] = "PARSER_EXCEPTION"
    finally:
        out["runtime_seconds"] = round(time.monotonic() - start, 3)
        if out["gpu_after"] is None:
            try:
                out["gpu_after"] = base.gpu_snapshot(torch)
            except Exception:
                pass
    return out

def record_key(record):
    return (record.get("utterance_id"), record.get("pair"), record.get("arm"))

def is_complete_record(record):
    return bool(record.get("generation_success") and record.get("parser_execution"))

def load_full_jsonl(path, planned_keys, lock_fingerprint):
    existing = {}
    if not path.exists():
        return existing
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception as e:
                raise RuntimeError(f"existing full JSONL line {line_number} is invalid: {e!r}")
            key = record_key(row)
            if key not in planned_keys:
                raise RuntimeError(f"existing full JSONL has out-of-plan key at line {line_number}: {key}")
            if key in existing:
                raise RuntimeError(f"existing full JSONL has duplicate primary key: {key}")
            if row.get("lock_fingerprint") != lock_fingerprint:
                raise RuntimeError(f"existing full JSONL line {line_number} has a different frozen lock fingerprint")
            existing[key] = row
    return existing

def append_checkpoint(path, record):
    try:
        line = json.dumps(base.jsonable(record), ensure_ascii=False, allow_nan=False)
    except Exception as e:
        fallback = {k: v for k, v in record.items() if isinstance(v, (str, int, float, bool)) or v is None}
        fallback.update({"failure_type": "SERIALIZATION_FAILURE", "generation_success": False,
                         "parser_execution": False, "failure_message": f"JSON serialization failed: {e!r}",
                         "traceback": traceback.format_exc()})
        line = json.dumps(fallback, ensure_ascii=False)
        record.clear()
        record.update(fallback)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())

def outcome_for_arm(record):
    if record is None:
        return "TECHNICAL_MISSING"
    if record.get("failure_type") == "PARSE_FAIL" or record.get("parser_status") == "PARSE_FAIL":
        return "PARSE_FAIL"
    if record.get("source_relation") == "CONSISTENT":
        return record.get("joint_outcome") or "TECHNICAL_MISSING"
    return record.get("joint_outcome") or "TECHNICAL_MISSING"

def paired_outcome_class(first, second, relation):
    if relation == "CONSISTENT":
        if "PARSE_FAIL" in (outcome_for_arm(first), outcome_for_arm(second)):
            return "PARSE_FAIL_INVOLVED"
        if "TECHNICAL_MISSING" in (outcome_for_arm(first), outcome_for_arm(second)):
            return "TECHNICAL_MISSING_INVOLVED"
        a = outcome_for_arm(first) == "SHARED_LABEL"
        b = outcome_for_arm(second) == "SHARED_LABEL"
        if a and b:
            return "PRESERVED_BOTH_ORDERS"
        if a:
            return "PRESERVED_ORDER_1_ONLY"
        if b:
            return "PRESERVED_ORDER_2_ONLY"
        return "NOT_PRESERVED"
    a, b = outcome_for_arm(first), outcome_for_arm(second)
    if "PARSE_FAIL" in (a, b):
        return "PARSE_FAIL_INVOLVED"
    if "TECHNICAL_MISSING" in (a, b):
        return "TECHNICAL_MISSING_INVOLVED"
    if "OTHER" in (a, b):
        return "OTHER_INVOLVED"
    if a == b == "SIDE_MODALITY_1":
        return "STABLE_MODALITY_1"
    if a == b == "SIDE_MODALITY_2":
        return "STABLE_MODALITY_2"
    if a == "SIDE_MODALITY_1" and b == "SIDE_MODALITY_2":
        return "SWITCH_FIRST_TO_SECOND"
    if a == "SIDE_MODALITY_2" and b == "SIDE_MODALITY_1":
        return "SWITCH_SECOND_TO_FIRST"
    return "OTHER_INVOLVED"

def metric_map(phase1_row, pair):
    m1, m2 = PAIR_MODALITIES[pair]
    key_by_modality = {"A": "A", "T": "T", "V": "V"}
    fields = {}
    for metric, prefix in (("entropy", "entropy"), ("margin", "margin"), ("sourceprob", "source_prob")):
        v1 = phase1_row.get(f"{prefix}_{key_by_modality[m1]}")
        v2 = phase1_row.get(f"{prefix}_{key_by_modality[m2]}")
        try:
            v1 = float(v1) if v1 not in (None, "") else None
        except (TypeError, ValueError):
            v1 = None
        try:
            v2 = float(v2) if v2 not in (None, "") else None
        except (TypeError, ValueError):
            v2 = None
        fields[f"{metric}_modality_1"] = v1
        fields[f"{metric}_modality_2"] = v2
        fields[f"delta_{metric}"] = (v1 - v2) if v1 is not None and v2 is not None else None
    return fields

def bootstrap_mean_ci(values, seed, n_boot=5000):
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not vals:
        return {"n": 0, "estimate": None, "ci95_low": None, "ci95_high": None}
    rng = random.Random(seed)
    n = len(vals)
    estimates = []
    for _ in range(n_boot):
        draw = [vals[rng.randrange(n)] for _ in range(n)]
        estimates.append(sum(draw) / n)
    estimates.sort()
    lo = estimates[int(0.025 * (n_boot - 1))]
    hi = estimates[int(0.975 * (n_boot - 1))]
    return {"n": n, "estimate": sum(vals) / n, "ci95_low": lo, "ci95_high": hi}

def bootstrap_ratio_ci(clusters, numerator_fn, denominator_fn, seed, n_boot=5000):
    if not clusters:
        return {"n_clusters": 0, "estimate": None, "ci95_low": None, "ci95_high": None}
    def ratio(rows):
        n = sum(numerator_fn(x) for x in rows)
        d = sum(denominator_fn(x) for x in rows)
        return n / d if d else None
    estimate = ratio(clusters)
    rng = random.Random(seed)
    n = len(clusters)
    vals = []
    for _ in range(n_boot):
        draw = [clusters[rng.randrange(n)] for _ in range(n)]
        value = ratio(draw)
        if value is not None:
            vals.append(value)
    vals.sort()
    if not vals:
        lo = hi = None
    else:
        lo = vals[int(0.025 * (len(vals) - 1))]
        hi = vals[int(0.975 * (len(vals) - 1))]
    return {"n_clusters": n, "estimate": estimate, "ci95_low": lo, "ci95_high": hi}

def build_analysis(full_records, all_rows):
    by_key = {record_key(r): r for r in full_records}
    phase1 = {r["utterance_id"]: r for r in base.read_csv(SAMPLE)}
    pair_specs = {pair: {"first": arms[0], "second": arms[1], "m1": PAIR_MODALITIES[pair][0],
                         "m2": PAIR_MODALITIES[pair][1]} for pair, arms in PAIR_ARMS.items()}
    planned_by_pair_uid = {}
    for row in all_rows:
        planned_by_pair_uid[(row["utterance_id"], row["pair"])] = row
    completeness, sample_rows, summaries, bootstrap_rows, emotion_rows = [], [], [], [], []
    for pair in ("AT", "AV", "VT"):
        spec = pair_specs[pair]
        uid_rows = sorted((row for (uid, p), row in planned_by_pair_uid.items() if p == pair), key=lambda x: x["utterance_id"])
        pair_cases = []
        for template in uid_rows:
            uid = template["utterance_id"]
            a = by_key.get((uid, pair, spec["first"]))
            b = by_key.get((uid, pair, spec["second"]))
            a_complete, b_complete = is_complete_record(a or {}), is_complete_record(b or {})
            relation = template["source_relation"]
            complete = a_complete and b_complete
            c = {"utterance_id": uid, "pair": pair, "source_relation": relation,
                 "y_modality_1": template["y_M1"], "y_modality_2": template["y_M2"],
                 "candidate_sequence_id": template["candidate_sequence_id"],
                 "order_1_arm": spec["first"], "order_2_arm": spec["second"],
                 "order_1_complete": a_complete, "order_2_complete": b_complete,
                 "pair_complete": complete, "order_1_parser_status": (a or {}).get("parser_status"),
                 "order_2_parser_status": (b or {}).get("parser_status"),
                 "order_1_failure_type": (a or {}).get("failure_type"),
                 "order_2_failure_type": (b or {}).get("failure_type"),
                 "order_1_outcome": outcome_for_arm(a), "order_2_outcome": outcome_for_arm(b)}
            completeness.append(c)
            m = metric_map(phase1.get(uid, {}), pair)
            paired = paired_outcome_class(a, b, relation)
            rec = {"utterance_id": uid, "pair": pair, "source_relation": relation,
                   "y_modality_1": template["y_M1"], "y_modality_2": template["y_M2"],
                   "prediction_order_1": (a or {}).get("parsed_label"),
                   "prediction_order_2": (b or {}).get("parsed_label"),
                   "outcome_order_1": outcome_for_arm(a), "outcome_order_2": outcome_for_arm(b),
                   "paired_outcome_class": paired,
                   "entropy_modality_1": m["entropy_modality_1"], "entropy_modality_2": m["entropy_modality_2"],
                   "delta_entropy": m["delta_entropy"], "margin_modality_1": m["margin_modality_1"],
                   "margin_modality_2": m["margin_modality_2"], "delta_margin": m["delta_margin"],
                   "sourceprob_modality_1": m["sourceprob_modality_1"],
                   "sourceprob_modality_2": m["sourceprob_modality_2"],
                   "delta_sourceprob": m["delta_sourceprob"],
                   "winner_minus_loser_entropy": None, "winner_minus_loser_margin": None,
                   "winner_minus_loser_sourceprob": None,
                   "trimodal_pattern": template["sample"].get("trimodal_pattern"),
                   "speaker_id": template["sample"].get("speaker_id"),
                   "official_split": template["sample"].get("official_split"),
                   "candidate_sequence_id": template["candidate_sequence_id"],
                   "technical_complete": complete}
            stable_side = None
            if relation == "CONFLICT" and complete and paired == "STABLE_MODALITY_1":
                stable_side = 1
            elif relation == "CONFLICT" and complete and paired == "STABLE_MODALITY_2":
                stable_side = 2
            if stable_side:
                winner, loser = (1, 2) if stable_side == 1 else (2, 1)
                for metric in ("entropy", "margin", "sourceprob"):
                    rec[f"winner_minus_loser_{metric}"] = m[f"{metric}_modality_{winner}"] - m[f"{metric}_modality_{loser}"] if m[f"{metric}_modality_{winner}"] is not None and m[f"{metric}_modality_{loser}"] is not None else None
            sample_rows.append(rec)
            pair_cases.append({"row": rec, "first": a, "second": b, "complete": complete})

        conflict = [x for x in pair_cases if x["row"]["source_relation"] == "CONFLICT" and x["complete"]]
        consistent = [x for x in pair_cases if x["row"]["source_relation"] == "CONSISTENT" and x["complete"]]
        summary = {"pair": pair, "DualReadable_N": EXPECTED_COUNTS[pair]["total"],
                   "conflict_N": EXPECTED_COUNTS[pair]["conflict"],
                   "consistent_N": EXPECTED_COUNTS[pair]["consistent"],
                   "pair_complete_conflict_N": len(conflict), "pair_complete_consistent_N": len(consistent)}
        conflict_categories = ("SIDE_MODALITY_1", "SIDE_MODALITY_2", "OTHER", "PARSE_FAIL")
        for order_idx, order_name in ((1, "order_1"), (2, "order_2")):
            outcomes = [outcome_for_arm(x["first"] if order_idx == 1 else x["second"]) for x in conflict]
            counts = Counter(outcomes)
            for category in conflict_categories:
                summary[f"{order_name}_{category}_N"] = counts.get(category, 0)
            n_side = counts.get("SIDE_MODALITY_1", 0) + counts.get("SIDE_MODALITY_2", 0)
            summary[f"{order_name}_side_choice_coverage"] = n_side / len(conflict) if conflict else None
            summary[f"{order_name}_modality_1_share_among_side_choices"] = counts.get("SIDE_MODALITY_1", 0) / n_side if n_side else None
            # Cluster bootstrap: resample pair-complete conflict utterances with both orders kept together.
            clusters = [{"outcome": outcome_for_arm(x["first"] if order_idx == 1 else x["second"])} for x in conflict]
            for metric_name, num, den in (
                ("side_choice_coverage", lambda z: z["outcome"] in ("SIDE_MODALITY_1", "SIDE_MODALITY_2"), lambda z: True),
                ("modality_1_share_among_side_choices", lambda z: z["outcome"] == "SIDE_MODALITY_1", lambda z: z["outcome"] in ("SIDE_MODALITY_1", "SIDE_MODALITY_2")),
            ):
                ci = bootstrap_ratio_ci(clusters, num, den, seed=20260927 + (0 if pair == "AT" else 100 if pair == "AV" else 200) + order_idx)
                bootstrap_rows.append({"pair": pair, "metric": f"{order_name}_{metric_name}", "bootstrap_unit": "utterance_id", **ci})
                summary[f"{order_name}_{metric_name}_ci95_low"] = ci["ci95_low"]
                summary[f"{order_name}_{metric_name}_ci95_high"] = ci["ci95_high"]
        paired_counts = Counter(x["row"]["paired_outcome_class"] for x in conflict)
        for category in ("STABLE_MODALITY_1", "STABLE_MODALITY_2", "SWITCH_FIRST_TO_SECOND", "SWITCH_SECOND_TO_FIRST", "OTHER_INVOLVED", "PARSE_FAIL_INVOLVED"):
            summary[f"{category}_N"] = paired_counts.get(category, 0)
        consistent_counts = Counter(x["row"]["paired_outcome_class"] for x in consistent)
        summary["consistent_preserved_both_orders_N"] = consistent_counts.get("PRESERVED_BOTH_ORDERS", 0)
        summary["consistent_shared_preservation_order_1"] = (sum(outcome_for_arm(x["first"]) == "SHARED_LABEL" for x in consistent) / len(consistent)) if consistent else None
        summary["consistent_shared_preservation_order_2"] = (sum(outcome_for_arm(x["second"]) == "SHARED_LABEL" for x in consistent) / len(consistent)) if consistent else None
        decisive = [x for x in conflict if outcome_for_arm(x["first"]) in ("SIDE_MODALITY_1", "SIDE_MODALITY_2") and outcome_for_arm(x["second"]) in ("SIDE_MODALITY_1", "SIDE_MODALITY_2")]
        paired_differences = []
        for x in decisive:
            a_side = 1 if outcome_for_arm(x["first"]) == "SIDE_MODALITY_1" else 0
            b_side = 1 if outcome_for_arm(x["second"]) == "SIDE_MODALITY_1" else 0
            paired_differences.append(a_side - b_side)
        effect_ci = bootstrap_mean_ci(paired_differences, seed=20260927 + (300 if pair == "AT" else 400 if pair == "AV" else 500))
        summary["paired_order_effect_modality_1_share_order1_minus_order2"] = effect_ci["estimate"]
        summary["paired_order_effect_n_both_side_choices"] = effect_ci["n"]
        summary["paired_order_effect_ci95_low"] = effect_ci["ci95_low"]
        summary["paired_order_effect_ci95_high"] = effect_ci["ci95_high"]
        for metric in ("entropy", "margin", "sourceprob"):
            vals = [x["row"][f"winner_minus_loser_{metric}"] for x in conflict if x["row"][f"winner_minus_loser_{metric}"] is not None]
            ci = bootstrap_mean_ci(vals, seed=20260927 + (600 if pair == "AT" else 700 if pair == "AV" else 800) + len(metric))
            summary[f"winner_minus_loser_{metric}_mean"] = ci["estimate"]
            summary[f"winner_minus_loser_{metric}_n"] = ci["n"]
            summary[f"winner_minus_loser_{metric}_ci95_low"] = ci["ci95_low"]
            summary[f"winner_minus_loser_{metric}_ci95_high"] = ci["ci95_high"]
            bootstrap_rows.append({"pair": pair, "metric": f"winner_minus_loser_{metric}", "bootstrap_unit": "utterance_id", **ci})
        summaries.append(summary)

        emotions = defaultdict(list)
        for x in conflict:
            left = str(x["row"]["y_modality_1"])
            right = str(x["row"]["y_modality_2"])
            emotions["|".join(sorted((left, right)))].append(x["row"]["paired_outcome_class"])
        for emotion_pair, classes in sorted(emotions.items()):
            cc = Counter(classes)
            emotion_rows.append({"pair": pair, "source_emotion_pair": emotion_pair, "pair_complete_conflict_N": len(classes),
                                 "stable_modality_1_N": cc.get("STABLE_MODALITY_1", 0),
                                 "stable_modality_2_N": cc.get("STABLE_MODALITY_2", 0),
                                 "switch_first_to_second_N": cc.get("SWITCH_FIRST_TO_SECOND", 0),
                                 "switch_second_to_first_N": cc.get("SWITCH_SECOND_TO_FIRST", 0),
                                 "other_involved_N": cc.get("OTHER_INVOLVED", 0),
                                 "parse_fail_involved_N": cc.get("PARSE_FAIL_INVOLVED", 0),
                                 "small_cell_flag_N_lt_10": len(classes) < 10})
    return completeness, sample_rows, summaries, bootstrap_rows, emotion_rows

def report_failure(path, status, reason, details=None):
    payload = {"EMOTIONTALK_PHASE2_PAIRWISE_FULL_RUN_V1_STATUS": status,
               "EMOTIONTALK_PHASE2_PAIRWISE_FULL_V1_STATUS": status,
               "reason": str(reason), "details": details or {},
               "created_utc": now(), "scientific_inference_attempted": 0,
               "PAIRWISE_SCIENCE_STATUS": "NOT_RUN",
               "NEXT_STEP": "STOP_FOR_REVIEW", "DO_NOT_RUN_PHASE3": True}
    dump_json(path, payload)

def load_runtime():
    import torch
    from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
    from qwen_omni_utils import process_mm_info
    model_dir = ROOT / "models/Qwen2.5-Omni-7B"
    processor = Qwen2_5OmniProcessor.from_pretrained(str(model_dir), local_files_only=True)
    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        str(model_dir), torch_dtype="auto", device_map="cuda",
        attn_implementation="flash_attention_2", local_files_only=True)
    model.eval()
    return torch, processor, model, process_mm_info, base.load_parser()

from src.emotiontalk.phase2 import core as base

remap_namespace(globals())
