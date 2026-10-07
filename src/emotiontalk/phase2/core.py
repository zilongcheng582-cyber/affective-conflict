from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate


import argparse

import csv

import hashlib

import importlib.util

import json

import os

import re

import subprocess

import sys

import time

import traceback

from collections import Counter

from datetime import datetime, timezone

from pathlib import Path

ROOT = project_root()

AUDIT = ROOT / "audit/EMOTIONTALK_CONTROLLED_V1"

PHASE1 = AUDIT / "phase1_competence_full_v1_2"

PRE = AUDIT / "pre_full_measurement_freeze_v1_2"

MEDIA = AUDIT / "media_freeze_v1"

OUT = AUDIT / "phase2_pairwise_gate_v1"

SAMPLE_CSV = PHASE1 / "EMOTIONTALK_PHASE1_SAMPLE_TABLE_V1_2.csv"

PHASE1_JSON = PHASE1 / "EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2.json"

PLAN_JSON = PHASE1 / "EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json"

PANEL_CSV = AUDIT / "EMOTIONTALK_MASTER_PANEL_V1.csv"

MEDIA_CSV = MEDIA / "EMOTIONTALK_MEDIA_MANIFEST_V1.csv"

PROMPT_PATH = ROOT / "code/prompts/emotiontalk_controlled_prompt_v1.json"

PARSER_PATH = ROOT / "code/benchmarks/emotiontalk_controlled_parser_v1.py"

CANDIDATE_PATH = AUDIT / "EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json"

TEXT_ROOT = ROOT / "data/EmotionTalk/extracted/Text/json"

RESOURCE_CSV = MEDIA / "EMOTIONTALK_VIDEO_RESOURCE_INVENTORY_V1.csv"

RUNNER_PHASE1 = ROOT / "code/run_qwen25_emotiontalk_phase1_v1_2.py"

ONTOLOGY = ("angry", "disgusted", "fearful", "happy", "neutral", "sad", "surprised")

PAIR_COLS = {"AT": ("audio_emotion", "text_emotion"),
             "AV": ("audio_emotion", "video_emotion"),
             "VT": ("video_emotion", "text_emotion")}

SAMPLE_PAIR_COLS = {"AT": ("y_A", "y_T"), "AV": ("y_A", "y_V"), "VT": ("y_V", "y_T")}

ARMS = {"AT": ("A_THEN_T", "T_THEN_A"),
        "AV": ("A_THEN_V", "V_THEN_A"),
        "VT": ("V_THEN_T", "T_THEN_V")}

ORDER = {"A_THEN_T": ("A", "T"), "T_THEN_A": ("T", "A"),
         "A_THEN_V": ("A", "V"), "V_THEN_A": ("V", "A"),
         "V_THEN_T": ("V", "T"), "T_THEN_V": ("T", "V")}

EXPECTED_HASHES = {
    "protocol_json": (AUDIT / "EMOTIONTALK_CONTROLLED_PROTOCOL_V1.json", "3c66b0a379fac6ce7aef8e27d589b9901825ec3c8db54dcda3e3b16772e60837"),
    "master_panel": (PANEL_CSV, "1ca8b79d8c146c6d807dd97a7bcd6cda519d5655e4cd0300afe7a92d159f406b"),
    "candidate_sequences": (CANDIDATE_PATH, "b249c68e92fa16ec7c41f617baffd1d293db8807b01b9c0f5d8490d41b790750"),
    "compositionality_spec": (PRE / "EMOTIONTALK_COMPOSITIONALITY_SPEC_V1_1.json", "91de88c803eb91280f4d25852ffb4fe7e70f89ea1c5abdbacef863f2919ef2dc"),
    "cross_regime_transfer_spec": (PRE / "CROSS_REGIME_TRANSFER_SPEC_V1.json", "73495ba69b346db05323179683e16cf7abdf88be86d26e9224d79050c50e0714"),
    "measurement_spec": (PRE / "EMOTIONTALK_MEASUREMENT_SPEC_V1_2.json", "e65eb6aa3fc1f7aafef4c7390dcf78443fa9dc8f7791e76af311e7734f117c18"),
    "media_manifest": (MEDIA_CSV, "c0343ac1cf79038dc5b9cfaf2cdebe9da3fbf13a18c24960656e2fabbd438c9d"),
    "media_freeze_report": (MEDIA / "EMOTIONTALK_MEDIA_FREEZE_V1.json", "02e8127e80e87a529ac713a006d04971b63d13b943e103efcf1d24f305725883"),
    "media_freeze_provenance": (MEDIA / "EMOTIONTALK_MEDIA_FREEZE_V1_PROVENANCE.json", "2d0ad33483ba955c9c13d4c699c2ee1e387b07411f09ba2b767279c840a7f6ad"),
    "prompt": (PROMPT_PATH, "ba6b71f080ea186a1494a54a0990a5740fc0aea69f008622618102f39efe55f8"),
    "parser": (PARSER_PATH, "c852f18279dd0d89fc8a97bab0516943775580a1a7dbcfe276e901d14ff7d374"),
    "phase1_runner": (RUNNER_PHASE1, "e9423fe9490c6a5eb7d6a771764d5678a97f5b6d55578215d3cc89dcf85c51b6"),
    "phase1_frozen_manifest": (PRE / "EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2_SHA256SUMS.txt", "e8e550a9587fd891fd94cac6cfef5210befa4e203accbe1d01352b5472f469fe"),
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_json(path):
    with Path(path).open(encoding="utf-8") as f:
        return relocate(json.load(f))

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return relocate(list(csv.DictReader(f)))

def find_key(obj, names):
    wanted = {re.sub(r"[^a-z0-9]", "", x.lower()) for x in names}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if re.sub(r"[^a-z0-9]", "", str(k).lower()) in wanted:
                return v
        for v in obj.values():
            got = find_key(v, names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find_key(v, names)
            if got is not None:
                return got
    return None

def as_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes"}

def resolve_media(value):
    p = Path(value)
    return p if p.is_absolute() else ROOT / p

def text_index(ids):
    wanted = set(ids)
    found = {}
    for path in sorted(TEXT_ROOT.rglob("*.json")):
        if path.stem in wanted and path.stem not in found:
            found[path.stem] = path
    missing = sorted(wanted - found.keys())
    if missing:
        raise RuntimeError(f"official Text JSON missing for IDs: {missing}")
    return found

def probe_streams(path):
    command = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)]
    p = subprocess.run(command, text=True, capture_output=True, check=True)
    streams = json.loads(p.stdout).get("streams", [])
    return {"video_stream_count": sum(s.get("codec_type") == "video" for s in streams),
            "audio_stream_count": sum(s.get("codec_type") == "audio" for s in streams)}

def jsonable(x):
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if hasattr(x, "detach"):
        x = x.detach().cpu()
        return jsonable(x.tolist())
    if hasattr(x, "item"):
        try:
            return x.item()
        except Exception:
            pass
    return str(x)

def dump_json(path, obj):
    Path(path).write_text(json.dumps(jsonable(obj), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def csv_write(path, rows, fields):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def load_parser():
    spec = importlib.util.spec_from_file_location("emotiontalk_frozen_parser", PARSER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_label

def population_preflight(phase1):
    plan = read_json(PLAN_JSON)
    rows = read_csv(SAMPLE_CSV)
    count = {pair: {"total": 0, "conflict": 0, "consistent": 0} for pair in PAIR_COLS}
    elig = {pair: [] for pair in PAIR_COLS}
    for r in rows:
        uid = r["utterance_id"]
        for pair, (m1, m2) in SAMPLE_PAIR_COLS.items():
            if not as_bool(r.get(f"DualReadable_{pair}")):
                continue
            count[pair]["total"] += 1
            stratum = "conflict" if r[m1] != r[m2] else "consistent"
            count[pair][stratum] += 1
            elig[pair].append((r, stratum))
    scalar_checks = {
        "planned": ("planned_records", "planned", 4500),
        "generation_success": ("generation_success_latest_record_per_slot", "generation_success", 4500),
        "parser_success": ("parser_execution_latest_record_per_slot", "parser_success", 4500),
        "candidate_score_success": ("candidate_score_success_latest_record_per_slot", "candidate_score_success", 4500),
        "technical_missing": ("technical_missing_latest_record_per_slot", "technical_missing", 0),
    }
    observed = {}
    for name, (k1, k2, expected) in scalar_checks.items():
        v = find_key(phase1, [k1, k2])
        observed[name] = v
        if v is None or int(v) != expected:
            raise ValueError(f"Phase 1 {name} mismatch: expected {expected}, observed {v}")
    if find_key(phase1, ["cuda_oom_all_attempts", "cuda_oom"]) not in (0, "0"):
        raise ValueError("Phase 1 CUDA OOM count is not zero")
    if count["AT"] != {"total": 397, "conflict": count["AT"]["conflict"], "consistent": count["AT"]["consistent"]} or count["AT"]["conflict"] + count["AT"]["consistent"] != 397:
        raise ValueError(f"AT population mismatch: {count['AT']}")
    if count["AV"]["total"] != 371 or count["AV"]["conflict"] + count["AV"]["consistent"] != 371:
        raise ValueError(f"AV population mismatch: {count['AV']}")
    if count["VT"]["total"] != 298 or count["VT"]["conflict"] + count["VT"]["consistent"] != 298:
        raise ValueError(f"VT population mismatch: {count['VT']}")
    memberships = sum(v["total"] for v in count.values())
    planned = find_key(plan, ["planned_phase2_joint_generations", "full_planned_generations", "planned_generations"])
    if memberships != 1066 or memberships * 2 != 2132 or planned is None or int(planned) != 2132:
        raise ValueError(f"Phase 2 population mismatch: memberships={memberships}, plan={planned}")
    readability = phase1.get("readability", {})
    for pair, expected in {"AT": 397, "AV": 371, "VT": 298}.items():
        summary = readability.get(f"DualReadable_{pair}")
        observed_n = summary.get("numerator") if isinstance(summary, dict) else summary
        if observed_n is None or int(observed_n) != expected:
            raise ValueError(f"Phase 1 summary {pair} mismatch: {summary}")
    triple = readability.get("TripleReadable")
    triple_n = triple.get("numerator") if isinstance(triple, dict) else triple
    if triple_n is None or int(triple_n) != 180:
        raise ValueError(f"Phase 1 TripleReadable mismatch: {triple}")
    return count, elig, memberships, plan, observed

def tensor_metadata(video_data, inputs):
    nframes = None
    if isinstance(video_data, (list, tuple)) and video_data:
        first = video_data[0]
        if isinstance(first, (list, tuple)):
            nframes = len(first)
        elif hasattr(first, "shape") and len(first.shape) >= 4:
            nframes = int(first.shape[0])
    meta = {"sampled_frame_count": nframes, "video_grid": None, "processed_dimensions": None, "processor_video_keys": []}
    for k, v in inputs.items():
        low = str(k).lower()
        if "video" in low or "grid_thw" in low or "second_per_grid" in low:
            meta["processor_video_keys"].append(str(k))
            if "grid_thw" in low:
                try:
                    meta["video_grid"] = jsonable(v)
                except Exception:
                    pass
            if "pixel_values_videos" in low and hasattr(v, "shape"):
                meta["processed_dimensions"] = list(v.shape)
    return meta

def gpu_snapshot(torch):
    try:
        if not torch.cuda.is_available():
            return {"available": False}
        return {"available": True, "device": torch.cuda.get_device_name(0),
                "allocated_bytes": int(torch.cuda.memory_allocated(0)),
                "reserved_bytes": int(torch.cuda.memory_reserved(0)),
                "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
                "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(0))}
    except Exception as e:
        return {"error": repr(e)}

def build_messages(rec, prompt_cfg):
    instruction = prompt_cfg["instruction_template"].format(candidate_labels=", ".join(rec["candidate_sequence"].split("|")))
    content = []
    for modality in (rec["evidence_1_modality"], rec["evidence_2_modality"]):
        if modality == "A":
            content.append({"type": "audio", "audio": rec["audio_path"]})
        elif modality == "V":
            content.append({"type": "video", "video": rec["silent_video_path"]})
        else:
            content.append({"type": "text", "text": "Text evidence:\n" + rec["sample"]["text"]})
    content.append({"type": "text", "text": instruction})
    return [{"role": "user", "content": content}]

def classify(parsed_label, m1, m2):
    if parsed_label not in ONTOLOGY:
        return "PARSE_FAIL"
    if m1 == m2:
        return "SHARED_LABEL" if parsed_label == m1 else "OTHER"
    if parsed_label == m1:
        return "SIDE_M1"
    if parsed_label == m2:
        return "SIDE_M2"
    return "OTHER"

remap_namespace(globals())
