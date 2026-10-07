from src.common.runtime import project_root, external_path, remap_namespace, relocate
import argparse

import copy

import math

import gc

import hashlib

import importlib.metadata as importlib_metadata

import json

import os

import platform

import shutil

import subprocess

import sys

import time

import traceback

from pathlib import Path

ROOT = project_root()

AUDIT = ROOT / "audit/EMOTIONTALK_CONTROLLED_V1"

MEDIA_FREEZE = AUDIT / "media_freeze_v1"

GATE_DIR = AUDIT / "pre_full_measurement_freeze_v1_2/attempt_4"

MODEL_DIR = ROOT / "models/Qwen2.5-Omni-7B"

ENV_PYTHON = ROOT / "envs/qwen25omni_recovered_v1/bin/python"

TEXT_ROOT = ROOT / "data/EmotionTalk/extracted/Text/json"

PROMPT_PATH = ROOT / "code/prompts/emotiontalk_controlled_prompt_v1.json"

PARSER_DIR = ROOT / "code/benchmarks"

PARSER_PATH = PARSER_DIR / "emotiontalk_controlled_parser_v1.py"

PARSER_TEST_PATH = PARSER_DIR / "test_emotiontalk_controlled_parser_v1.py"

RUNNER_PATH = ROOT / "code/run_qwen25_emotiontalk_phase1_v1_2.py"

PROTOCOL_MD = AUDIT / "EMOTIONTALK_CONTROLLED_PROTOCOL_V1.md"

PROTOCOL_JSON = AUDIT / "EMOTIONTALK_CONTROLLED_PROTOCOL_V1.json"

PANEL_CSV = AUDIT / "EMOTIONTALK_MASTER_PANEL_V1.csv"

CANDIDATE_JSON = AUDIT / "EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json"

CALIBRATION_CSV = MEDIA_FREEZE / "EMOTIONTALK_VIDEO_CALIBRATION_CANDIDATES_V1.csv"

MEDIA_MANIFEST = MEDIA_FREEZE / "EMOTIONTALK_MEDIA_MANIFEST_V1.csv"

FREEZE_REPORT = MEDIA_FREEZE / "EMOTIONTALK_MEDIA_FREEZE_V1.json"

FREEZE_PROVENANCE = MEDIA_FREEZE / "EMOTIONTALK_MEDIA_FREEZE_V1_PROVENANCE.json"

OFFICIAL_REPO = ROOT / "external/EmotionTalk"

EXPECTED_COMMIT = "cb8397e226ce7c1fccee41ea21161a3f98f578e1"

ONTOLOGY = ("angry", "disgusted", "fearful", "happy", "neutral", "sad", "surprised")

TIERS = ("LOW", "MEDIAN", "P90", "P95", "P99", "MAX")

ARMS = ("T_ONLY", "A_ONLY", "V_ONLY")

PLANNED_RECORDS = len(TIERS) * len(ARMS)

MAX_NEW_TOKENS = 16

ATTENTION_IMPLEMENTATION = "flash_attention_2"

DEVICE_MAP = "cuda"

OMP_ORIGINAL = os.environ.get("OMP_NUM_THREADS")

try:
    _omp_value=int(OMP_ORIGINAL) if OMP_ORIGINAL is not None else 1
except (TypeError,ValueError):
    _omp_value=0
OMP_OVERRIDDEN = _omp_value <= 0

OMP_EFFECTIVE = os.environ.get("OMP_NUM_THREADS", "1")

REPORT_JSON = GATE_DIR / "EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2.json"

REPORT_MD = GATE_DIR / "EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2.md"

PROVENANCE_JSON = GATE_DIR / "EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2_PROVENANCE.json"

RESULTS_JSONL = GATE_DIR / "emotiontalk_phase1_measurement_gate_v1_2.jsonl"

class GateAbort(RuntimeError):
    def __init__(self, status, message, details=None):
        super().__init__(message)
        self.status = status
        self.details = details or {}

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def read_csv(path):
    import csv
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return relocate(list(csv.DictReader(handle)))

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)

def normalize_template_result(value):
    if isinstance(value, str):
        return value, "str"
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value[0], "singleton_list_str"
    raise TypeError("chat template must return str or singleton list[str]")

def run_parser_static_tests(parse_label):
    cases = [
        ("happy", "happy", "OK"),
        ("Happy", "happy", "OK"),
        (" happy ", "happy", "OK"),
        ("The answer is happy.", None, "PARSE_FAIL"),
        ("unknown text", None, "PARSE_FAIL"),
        ("happy sad", None, "PARSE_FAIL"),
    ]
    for raw, expected_label, expected_status in cases:
        result = parse_label(raw)
        if result.get("parsed_label") != expected_label or result.get("parser_status") != expected_status:
            raise GateAbort("TECHNICAL_FAILURE", "parser static contract test failed",
                            {"raw_case": raw, "result": result})
        if result.get("raw_text") != raw:
            raise GateAbort("TECHNICAL_FAILURE", "parser did not preserve raw_text",
                            {"raw_case": raw, "result": result})
    if normalize_template_result("rendered") != ("rendered", "str"):
        raise GateAbort("TECHNICAL_FAILURE", "str chat-template normalization test failed")
    if normalize_template_result(["rendered"]) != ("rendered", "singleton_list_str"):
        raise GateAbort("TECHNICAL_FAILURE", "singleton list[str] chat-template normalization test failed")
    return {"parser_cases": len(cases), "str_template_result": "PASS",
            "singleton_list_str_template_result": "PASS"}

def find_text_jsons(utterance_ids):
    remaining = set(utterance_ids)
    found = {}
    if not TEXT_ROOT.is_dir():
        raise GateAbort("TECHNICAL_FAILURE", "official Text JSON root is missing",
                        {"text_root": str(TEXT_ROOT)})
    for path in TEXT_ROOT.rglob("*.json"):
        uid = path.stem
        if uid in remaining:
            found[uid] = path
            remaining.remove(uid)
            if not remaining:
                break
    if remaining:
        raise GateAbort("TECHNICAL_FAILURE", "official Text.content JSON not found for gate samples",
                        {"missing_utterance_ids": sorted(remaining)})
    return found

def ffprobe_stream_contract(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise GateAbort("TECHNICAL_FAILURE", "ffprobe is unavailable")
    command = [ffprobe, "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise GateAbort("TECHNICAL_FAILURE", "silent-video ffprobe failed",
                        {"path": str(path), "returncode": completed.returncode,
                         "stderr": completed.stderr[-4000:]})
    streams = json.loads(completed.stdout).get("streams", [])
    return {
        "video_stream_count": sum(x.get("codec_type") == "video" for x in streams),
        "audio_stream_count": sum(x.get("codec_type") == "audio" for x in streams),
    }

def validate_frozen_inputs():
    required = [
        PROTOCOL_MD, PROTOCOL_JSON, PANEL_CSV, CANDIDATE_JSON, CALIBRATION_CSV,
        MEDIA_MANIFEST, FREEZE_REPORT, FREEZE_PROVENANCE, PROMPT_PATH, PARSER_PATH,
        PARSER_TEST_PATH, RUNNER_PATH,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise GateAbort("TECHNICAL_FAILURE", "required frozen gate input is missing",
                        {"missing_paths": missing})
    protocol = read_json(PROTOCOL_JSON)
    freeze_report = read_json(FREEZE_REPORT)
    freeze_provenance = read_json(FREEZE_PROVENANCE)
    candidate_data = read_json(CANDIDATE_JSON)
    prompt = read_json(PROMPT_PATH)

    expected_statuses = {
        "EMOTIONTALK_CONTROLLED_PROTOCOL_V1_STATUS": "FROZEN",
        "EMOTIONTALK_MASTER_PANEL_V1_STATUS": "FROZEN",
        "EMOTIONTALK_SCIENCE_STATUS": "NOT_RUN",
    }
    status_mismatches = {
        key: {"expected": value, "actual": protocol.get(key)}
        for key, value in expected_statuses.items() if protocol.get(key) != value
    }
    media_status = freeze_report.get("EMOTIONTALK_MASTER_PANEL_MEDIA_FREEZE_STATUS")
    if media_status != "PASS" or freeze_provenance.get("freeze_status") != "PASS":
        status_mismatches["EMOTIONTALK_MASTER_PANEL_MEDIA_FREEZE_STATUS"] = {
            "expected": "PASS", "report": media_status,
            "provenance": freeze_provenance.get("freeze_status"),
        }
    if status_mismatches:
        raise GateAbort("TECHNICAL_FAILURE", "frozen protocol or media status precondition failed",
                        {"status_mismatches": status_mismatches})
    if protocol.get("MODEL_INFERENCE_RUN") is not False:
        raise GateAbort("TECHNICAL_FAILURE", "protocol indicates a prior inference run")

    hashes = {
        "protocol_md_sha256": sha256_file(PROTOCOL_MD),
        "protocol_json_sha256": sha256_file(PROTOCOL_JSON),
        "master_panel_sha256": sha256_file(PANEL_CSV),
        "candidate_sequences_sha256": sha256_file(CANDIDATE_JSON),
        "media_manifest_sha256": sha256_file(MEDIA_MANIFEST),
        "media_freeze_report_sha256": sha256_file(FREEZE_REPORT),
        "media_freeze_provenance_sha256": sha256_file(FREEZE_PROVENANCE),
        "calibration_candidates_sha256": sha256_file(CALIBRATION_CSV),
        "prompt_sha256": sha256_file(PROMPT_PATH),
        "parser_sha256": sha256_file(PARSER_PATH),
        "parser_tests_sha256": sha256_file(PARSER_TEST_PATH),
        "runner_sha256": sha256_file(RUNNER_PATH),
    }
    expected_hashes = {
        "protocol_json_sha256": freeze_provenance.get("protocol_sha256"),
        "master_panel_sha256": freeze_provenance.get("master_panel_sha256"),
        "candidate_sequences_sha256": freeze_provenance.get("candidate_sequences_sha256"),
    }
    mismatches = {
        key: {"current": hashes[key], "frozen": expected}
        for key, expected in expected_hashes.items() if expected != hashes[key]
    }
    if mismatches:
        raise GateAbort("BLOCKED_HASH_MISMATCH", "frozen protocol/panel/candidate hash mismatch",
                        {"hash_mismatches": mismatches})
    if candidate_data.get("status") != "FROZEN":
        raise GateAbort("BLOCKED_HASH_MISMATCH", "candidate sequence file is not frozen")
    if freeze_provenance.get("official_repo_commit") != EXPECTED_COMMIT:
        raise GateAbort("BLOCKED_HASH_MISMATCH", "official repository commit differs from frozen provenance")
    try:
        actual_commit = subprocess.check_output(
            ["git", "-C", str(OFFICIAL_REPO), "rev-parse", "HEAD"], text=True
        ).strip()
        worktree_status = subprocess.check_output(
            ["git", "-C", str(OFFICIAL_REPO), "status", "--short"], text=True
        ).strip()
    except Exception as exc:
        raise GateAbort("TECHNICAL_FAILURE", "could not verify official repository identity",
                        {"exception": str(exc)})
    if actual_commit != EXPECTED_COMMIT or worktree_status:
        raise GateAbort("BLOCKED_HASH_MISMATCH", "official repository is not at the clean frozen commit",
                        {"expected_commit": EXPECTED_COMMIT, "actual_commit": actual_commit,
                         "worktree_status": worktree_status})

    if prompt.get("ontology") != list(ONTOLOGY):
        raise GateAbort("TECHNICAL_FAILURE", "prompt ontology differs from frozen source ontology")
    if set(prompt.get("templates", {})) != set(ARMS):
        raise GateAbort("TECHNICAL_FAILURE", "prompt does not define exactly the three unimodal gate arms")
    if "candidate_labels" not in prompt.get("instruction_template", ""):
        raise GateAbort("TECHNICAL_FAILURE", "prompt instruction omits frozen candidate sequence")

    panel_rows = read_csv(PANEL_CSV)
    manifest_rows = read_csv(MEDIA_MANIFEST)
    calibration_rows = read_csv(CALIBRATION_CSV)
    panel = {row["utterance_id"]: row for row in panel_rows}
    manifest = {row["utterance_id"]: row for row in manifest_rows}
    if len(panel) != 1500 or len(panel_rows) != 1500:
        raise GateAbort("TECHNICAL_FAILURE", "master panel count or unique ID check failed")
    if len(manifest) != 1500 or len(manifest_rows) != 1500:
        raise GateAbort("TECHNICAL_FAILURE", "media manifest count or unique ID check failed")
    tier_counts = {}
    for row in calibration_rows:
        tier_counts[row.get("tier")] = tier_counts.get(row.get("tier"), 0) + 1
    if len(calibration_rows) != 6 or tier_counts != {tier: 1 for tier in TIERS}:
        raise GateAbort("TECHNICAL_FAILURE", "calibration file must contain one frozen sample per tier",
                        {"tier_counts": tier_counts, "rows": len(calibration_rows)})
    candidate_sequences = {row["candidate_sequence_id"]: row["pipe"]
                           for row in candidate_data.get("sequences", [])}
    if len(candidate_sequences) != 14:
        raise GateAbort("BLOCKED_HASH_MISMATCH", "frozen candidate sequence catalog is incomplete")
    selected_by_tier = {row["tier"]: row for row in calibration_rows}
    text_paths = find_text_jsons([row["utterance_id"] for row in calibration_rows])
    frozen_video_hashes = freeze_provenance.get("all_derived_file_sha256", {})
    selected = []
    video_probes = {}
    for tier in TIERS:
        candidate = selected_by_tier[tier]
        uid = candidate["utterance_id"]
        if uid not in panel or uid not in manifest:
            raise GateAbort("TECHNICAL_FAILURE", "calibration utterance is absent from panel or manifest",
                            {"tier": tier, "utterance_id": uid})
        p_row, m_row = panel[uid], manifest[uid]
        sequence_id = p_row["candidate_sequence_id"]
        sequence_pipe = p_row["candidate_sequence"]
        labels = sequence_pipe.split("|")
        if (sequence_id not in candidate_sequences or candidate_sequences[sequence_id] != sequence_pipe or
                len(labels) != 7 or len(set(labels)) != 7 or set(labels) != set(ONTOLOGY)):
            raise GateAbort("BLOCKED_HASH_MISMATCH", "sample candidate sequence differs from frozen sequence catalog",
                            {"tier": tier, "utterance_id": uid, "candidate_sequence_id": sequence_id})
        if p_row["audio_path"] != m_row["audio_path"] or p_row["video_path"] != m_row["source_av_video_path"]:
            raise GateAbort("BLOCKED_HASH_MISMATCH", "panel and media manifest path mismatch",
                            {"tier": tier, "utterance_id": uid})
        audio_path = Path(p_row["audio_path"])
        silent_path = Path(m_row["silent_video_path"])
        if not audio_path.is_file() or audio_path.stat().st_size <= 0:
            raise GateAbort("TECHNICAL_FAILURE", "standalone audio is missing or empty",
                            {"tier": tier, "utterance_id": uid, "audio_path": str(audio_path)})
        if not silent_path.is_file() or silent_path.stat().st_size <= 0:
            raise GateAbort("TECHNICAL_FAILURE", "silent video is missing or empty",
                            {"tier": tier, "utterance_id": uid, "silent_video_path": str(silent_path)})
        if m_row.get("validation_status") != "PASS" or m_row.get("silent_audio_stream_count") != "0":
            raise GateAbort("BLOCKED_HASH_MISMATCH", "media manifest does not certify a silent-video input",
                            {"tier": tier, "utterance_id": uid})
        manifest_hash = m_row.get("silent_video_sha256")
        provenance_hash = frozen_video_hashes.get(uid)
        actual_hash = sha256_file(silent_path)
        if not (manifest_hash and provenance_hash and actual_hash == manifest_hash == provenance_hash):
            raise GateAbort("BLOCKED_HASH_MISMATCH", "selected silent-video hash differs from freeze provenance",
                            {"tier": tier, "utterance_id": uid,
                             "manifest_hash": manifest_hash, "provenance_hash": provenance_hash,
                             "actual_hash": actual_hash})
        text_path = text_paths[uid]
        text_json = read_json(text_path)
        official_text = text_json.get("content") if isinstance(text_json, dict) else None
        if not isinstance(official_text, str) or official_text != p_row["text"]:
            raise GateAbort("BLOCKED_HASH_MISMATCH", "panel text differs from official Text.content",
                            {"tier": tier, "utterance_id": uid, "text_json_path": str(text_path)})
        probe = ffprobe_stream_contract(silent_path)
        video_probes[uid] = probe
        if probe["video_stream_count"] < 1 or probe["audio_stream_count"] != 0:
            raise GateAbort("TECHNICAL_FAILURE", "V_ONLY silent-video stream contract failed",
                            {"tier": tier, "utterance_id": uid, "probe": probe})
        selected.append({
            "resource_tier": tier,
            "utterance_id": uid,
            "candidate_sequence_id": sequence_id,
            "candidate_sequence": sequence_pipe,
            "candidate_labels": labels,
            "text_emotion": p_row["text_emotion"],
            "audio_emotion": p_row["audio_emotion"],
            "video_emotion": p_row["video_emotion"],
            "text": official_text,
            "text_json_path": str(text_path),
            "audio_path": str(audio_path),
            "silent_video_path": str(silent_path),
            "media_manifest_video_sha256": actual_hash,
            "video_stream_probe": probe,
        })
    return {
        "prompt": prompt,
        "hashes": hashes,
        "selected_samples": selected,
        "video_contract_all_pass": len(video_probes) == 6,
        "video_probes": video_probes,
        "official_repo_commit": actual_commit,
    }

def build_messages(sample, arm, prompt_config):
    instruction = prompt_config["instruction_template"].format(
        candidate_labels=", ".join(sample["candidate_labels"])
    )
    if arm == "T_ONLY":
        prompt_text = prompt_config["templates"][arm].format(
            instruction=instruction, text_evidence=sample["text"]
        )
        content = [{"type": "text", "text": prompt_text}]
        evidence_path = sample["text_json_path"]
    elif arm == "A_ONLY":
        prompt_text = prompt_config["templates"][arm].format(instruction=instruction)
        content = [{"type": "audio", "audio": sample["audio_path"]},
                   {"type": "text", "text": prompt_text}]
        evidence_path = sample["audio_path"]
    elif arm == "V_ONLY":
        prompt_text = prompt_config["templates"][arm].format(instruction=instruction)
        content = [{"type": "video", "video": sample["silent_video_path"]},
                   {"type": "text", "text": prompt_text}]
        evidence_path = sample["silent_video_path"]
    else:
        raise ValueError("unsupported gate arm")
    return [{"role": "user", "content": content}], prompt_text, evidence_path

def tensor_summary(value, include_small_grid_values=False):
    if hasattr(value, "shape"):
        shape = [int(x) for x in value.shape]
        result = {"type": type(value).__name__, "shape": shape,
                  "dtype": str(getattr(value, "dtype", "unknown"))}
        if include_small_grid_values and hasattr(value, "numel") and int(value.numel()) <= 24:
            try:
                result["values"] = value.detach().cpu().tolist()
            except Exception:
                pass
        return result
    if isinstance(value, dict):
        return {str(k): tensor_summary(v, include_small_grid_values) for k, v in list(value.items())[:12]}
    if isinstance(value, (list, tuple)):
        return {"type": type(value).__name__, "length": len(value),
                "first_items": [tensor_summary(x, include_small_grid_values) for x in list(value)[:3]]}
    return {"type": type(value).__name__}

def count_video_frames(video_data):
    if video_data is None:
        return None
    items = video_data if isinstance(video_data, (list, tuple)) else [video_data]
    if not items:
        return 0
    first = items[0]
    if isinstance(first, (list, tuple)):
        return len(first)
    if hasattr(first, "shape"):
        shape = list(first.shape)
        if len(shape) >= 4:
            return int(shape[0])
    return None

def video_processing_metadata(video_data, processor_inputs):
    video_keys = {}
    resolution = None
    grid_frames = None
    for key, value in processor_inputs.items():
        lower = str(key).lower()
        if "video" in lower or "grid_thw" in lower or "second_per_grid" in lower:
            video_keys[str(key)] = tensor_summary(value, include_small_grid_values=("grid_thw" in lower))
            if "pixel_values_videos" in lower and hasattr(value, "shape") and len(value.shape) >= 3:
                shape = [int(x) for x in value.shape]
                resolution = {"height": shape[-2], "width": shape[-1]}
            if "video_grid_thw" in lower and hasattr(value, "shape"):
                try:
                    grid = value.detach().cpu().tolist()
                    if isinstance(grid, list):
                        grid_frames = sum(int(row[0]) for row in grid if isinstance(row, list) and row)
                except Exception:
                    pass
    return {
        "sampled_frame_count_estimate": grid_frames or count_video_frames(video_data),
        "processed_resolution": resolution,
        "video_data_structure": tensor_summary(video_data),
        "video_tensor_grid_metadata": video_keys,
        "sampling_parameters": "Qwen2.5-Omni/qwen-omni-utils defaults; no FPS, pixel, frame-count, or resolution override",
    }

def gpu_memory_snapshot(torch):
    if not torch.cuda.is_available():
        return {"cuda_available": False}
    try:
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        return {"cuda_available": True, "gpu_name": torch.cuda.get_device_name(0),
                "total_bytes": int(total_bytes), "free_bytes": int(free_bytes),
                "allocated_bytes": int(torch.cuda.memory_allocated(0)),
                "reserved_bytes": int(torch.cuda.memory_reserved(0))}
    except Exception as exc:
        return {"cuda_available": True, "telemetry_error": str(exc)}

def append_jsonl(path, record):
    encoded = json.dumps(record, ensure_ascii=False, allow_nan=False)
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(encoded + "\n")
        handle.flush()
        os.fsync(handle.fileno())

def tokenizer_ids(tokenizer, text):
    encoded = tokenizer(text, add_special_tokens=False)
    ids = encoded["input_ids"]
    if ids and isinstance(ids[0], list):
        if len(ids) != 1:
            raise RuntimeError("tokenizer unexpectedly returned multiple rows")
        ids = ids[0]
    return [int(x) for x in ids]

def stable_softmax(values):
    peak = max(values)
    exps = [math.exp(x - peak) for x in values]
    total = sum(exps)
    return [x / total for x in exps]

def score_candidate_strings(rendered, inputs, sample, arm, processor, model, torch):
    """Score exact canonical continuations with the same thinker used by Omni generate()."""
    tokenizer = processor.tokenizer
    labels = list(sample["candidate_labels"])
    if len(labels) != 7 or len(set(labels)) != 7 or set(labels) != set(ONTOLOGY):
        raise RuntimeError("candidate labels do not equal the frozen seven-label ontology")
    prefix_ids = tokenizer_ids(tokenizer, rendered)
    actual_ids = [int(x) for x in inputs["input_ids"][0].detach().cpu().tolist()]
    suffix_n = min(16, len(prefix_ids), len(actual_ids))
    if suffix_n < 1 or prefix_ids[-suffix_n:] != actual_ids[-suffix_n:]:
        raise RuntimeError("assistant-generation prefix suffix tokenization differs from model input IDs")
    continuations = {}
    for label in labels:
        full_ids = tokenizer_ids(tokenizer, rendered + label)
        if full_ids[:len(prefix_ids)] != prefix_ids:
            raise RuntimeError(f"candidate boundary changes prefix tokenization: {label}")
        suffix = full_ids[len(prefix_ids):]
        if not suffix:
            raise RuntimeError(f"empty candidate continuation: {label}")
        continuations[label] = suffix

    base_inputs = dict(inputs)
    attention = base_inputs.get("attention_mask")
    if attention is None:
        attention = torch.ones_like(base_inputs["input_ids"], dtype=torch.long)
    prefix_len = int(attention[0].sum().item())
    if prefix_len < 1:
        raise RuntimeError("empty attention-masked prefix")
    base_ids = base_inputs["input_ids"][:, :prefix_len]
    base_attention = attention[:, :prefix_len]
    base_inputs["input_ids"] = base_ids
    base_inputs["attention_mask"] = base_attention
    with torch.inference_mode():
        base = model.thinker(**base_inputs, use_cache=False, use_audio_in_video=False)
        base_log_probs = torch.log_softmax(base.logits[0, prefix_len - 1].float(), dim=-1)
        del base
        score_rows = {}
        forward_calls = 1
        for label in labels:
            ids = continuations[label]
            if len(ids) == 1:
                token_logps = [float(base_log_probs[ids[0]].item())]
            else:
                suffix_tensor = torch.tensor([ids], dtype=base_ids.dtype, device=base_ids.device)
                candidate_inputs = dict(base_inputs)
                candidate_inputs["input_ids"] = torch.cat([base_ids, suffix_tensor], dim=1)
                candidate_inputs["attention_mask"] = torch.cat([
                    base_attention,
                    torch.ones((1, len(ids)), dtype=base_attention.dtype, device=base_attention.device)
                ], dim=1)
                candidate_out = model.thinker(**candidate_inputs, use_cache=False,
                                              use_audio_in_video=False)
                forward_calls += 1
                token_logps = []
                for idx, token_id in enumerate(ids):
                    pred_pos = prefix_len - 1 + idx
                    token_log_probs = torch.log_softmax(candidate_out.logits[0, pred_pos].float(), dim=-1)
                    token_logps.append(float(token_log_probs[token_id].item()))
                    del token_log_probs
                del candidate_out, candidate_inputs, suffix_tensor
            raw_score = float(sum(token_logps))
            mean_score = raw_score / len(token_logps)
            score_rows[label] = {
                "token_ids": ids,
                "token_count": len(ids),
                "token_log_probabilities": token_logps,
                "sum_log_probability": raw_score,
                "mean_token_log_probability": mean_score,
            }
        del base_log_probs
    raw_scores = [score_rows[label]["sum_log_probability"] for label in labels]
    mean_scores = [score_rows[label]["mean_token_log_probability"] for label in labels]
    probs_raw = stable_softmax(raw_scores)
    probs_mean = stable_softmax(mean_scores)
    for i, label in enumerate(labels):
        score_rows[label]["probability_sum_score_sensitivity"] = probs_raw[i]
        score_rows[label]["probability_mean_score_primary"] = probs_mean[i]

    def entropy(p):
        h = -sum(x * math.log(x) for x in p if x > 0)
        return {"nats": h, "normalized_by_log7": h / math.log(7)}

    order = sorted(range(7), key=lambda i: (-probs_mean[i], i))
    top1, top2 = order[:2]
    raw_order = sorted(range(7), key=lambda i: (-probs_raw[i], i))
    source_field = {"T_ONLY": "text_emotion", "A_ONLY": "audio_emotion", "V_ONLY": "video_emotion"}[arm]
    source_label = sample[source_field]
    if source_label not in labels:
        raise RuntimeError(f"source-side label outside candidate ontology: {source_label}")
    source_idx = labels.index(source_label)
    return {
        "candidate_scoring_status": "OK",
        "candidate_scoring_method": "thinker_teacher_forced_exact_sequence_sum_and_mean_log_probability",
        "candidate_scoring_prefix_token_count": len(prefix_ids),
        "candidate_scoring_forward_calls": forward_calls,
        "candidate_token_counts": {label: len(continuations[label]) for label in labels},
        "candidate_scores": score_rows,
        "candidate_probability_method_primary": "softmax(mean_token_log_probability)",
        "candidate_probability_method_sensitivity": "softmax(sum_log_probability)",
        "candidate_score_argmax_primary": labels[top1],
        "candidate_score_argmax_sum_sensitivity": labels[raw_order[0]],
        "candidate_top1_primary": labels[top1],
        "candidate_top1_probability_primary": probs_mean[top1],
        "candidate_top2_primary": labels[top2],
        "candidate_top2_probability_primary": probs_mean[top2],
        "candidate_top1_top2_margin_primary": probs_mean[top1] - probs_mean[top2],
        "candidate_entropy_primary": entropy(probs_mean),
        "candidate_entropy_sum_sensitivity": entropy(probs_raw),
        "source_label_for_measurement_only": source_label,
        "source_label_probability_primary": probs_mean[source_idx],
        "source_label_probability_sum_sensitivity": probs_raw[source_idx],
        "score_greedy_parser_agreement": None,
    }

def perform_arm(sample, arm, prompt_config, processor, model, torch, process_mm_info, parse_label, counters):
    started = time.perf_counter()
    counters["attempted_record_count"] += 1
    record = {
        "gate_record_index": counters["attempted_record_count"],
        "utterance_id": sample["utterance_id"],
        "resource_tier": sample["resource_tier"],
        "arm": arm,
        "candidate_sequence_id": sample["candidate_sequence_id"],
        "candidate_sequence": sample["candidate_sequence"],
        "text": sample["text"] if arm == "T_ONLY" else None,
        "input_text_reference": sample["text_json_path"] if arm == "T_ONLY" else None,
        "audio_path": sample["audio_path"],
        "silent_video_path": sample["silent_video_path"],
        "evidence_path_used": None,
        "video_input_contract": "derived_silent_video_only" if arm == "V_ONLY" else None,
        "generation_attempted": False,
        "generation_success": False,
        "raw_generation": None,
        "parser_execution": False,
        "parsed_label": None,
        "parser_status": None,
        "failure_type": None,
        "failure_message": None,
        "failure_traceback": None,
        "runtime_seconds": None,
        "gpu_memory_before": gpu_memory_snapshot(torch),
        "gpu_memory_after_generation_or_error": None,
        "gpu_memory_after_cleanup": None,
        "video_processing_metadata": None,
        "generation_config": {
            "do_sample": False,
            "temperature_passed": False,
            "temperature_behavior": "not passed; deterministic greedy decoding",
            "max_new_tokens": MAX_NEW_TOKENS,
            "dtype_requested": "auto",
            "dtype_resolved": str(model.dtype),
            "device_map": DEVICE_MAP,
            "attention_implementation": ATTENTION_IMPLEMENTATION,
            "return_audio": False,
            "use_audio_in_video": False,
        },
    }
    stage = "CHAT_TEMPLATE"
    inputs = generated_ids = trimmed_ids = decoded = None
    audios = images = videos = None
    messages = None
    try:
        messages, _, evidence_path = build_messages(sample, arm, prompt_config)
        record["evidence_path_used"] = evidence_path
        rendered_raw = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        rendered, rendered_type = normalize_template_result(rendered_raw)
        record["chat_template_return_type"] = rendered_type
        stage = "MEDIA_DECODE"
        audios, images, videos = process_mm_info(messages, use_audio_in_video=False)
        if arm == "V_ONLY":
            record["video_processing_metadata"] = {
                "preprocessor_video_structure": tensor_summary(videos),
                "sampled_frame_count_estimate_from_preprocessor": count_video_frames(videos),
                "sampling_parameters": "Qwen2.5-Omni/qwen-omni-utils defaults; no overrides",
            }
        stage = "PROCESSOR"
        inputs = processor(text=rendered, audio=audios, images=images, videos=videos,
                           return_tensors="pt", padding=True, use_audio_in_video=False)
        if arm == "V_ONLY":
            record["video_processing_metadata"] = video_processing_metadata(videos, inputs)
        stage = "GENERATION"
        inputs = inputs.to(model.device).to(model.dtype)
        record["generation_attempted"] = True
        counters["generation_attempt_count"] += 1
        generated_ids = model.generate(
            **inputs, do_sample=False, max_new_tokens=MAX_NEW_TOKENS,
            use_audio_in_video=False, return_audio=False,
        )
        torch.cuda.synchronize()
        record["gpu_memory_after_generation_or_error"] = gpu_memory_snapshot(torch)
        stage = "OUTPUT_DECODE"
        trimmed_ids = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        decoded = processor.batch_decode(
            trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        if not isinstance(decoded, list) or len(decoded) != 1 or not isinstance(decoded[0], str):
            raise TypeError("batch_decode must return a singleton list[str]")
        raw_generation = decoded[0]
        record["generation_success"] = True
        record["raw_generation"] = raw_generation
        counters["generation_success_count"] += 1
        stage = "PARSER"
        counters["parser_execution_count"] += 1
        record["parser_execution"] = True
        record["parser_execution_success"] = False
        try:
            parsed = parse_label(raw_generation)
            if not isinstance(parsed, dict) or parsed.get("parser_status") not in ("OK", "PARSE_FAIL"):
                raise TypeError("parser returned an invalid parser_status")
            record["parsed_label"] = parsed.get("parsed_label")
            record["parser_status"] = parsed.get("parser_status")
            record["parser_execution_success"] = True
            if record["parser_status"] == "PARSE_FAIL":
                counters["parse_failures"] += 1
            else:
                counters["parse_successes"] += 1
        except Exception as parser_exc:
            record["parser_status"] = "PARSER_EXCEPTION"
            record["parser_failure_message"] = str(parser_exc)
            record["parser_failure_traceback"] = traceback.format_exc()
            record["failure_type"] = "PARSER_EXECUTION_FAILURE"
            counters["parser_execution_failure_count"] += 1
        stage = "UNCERTAINTY_SCORING"
        score_result = score_candidate_strings(rendered, inputs, sample, arm, processor, model, torch)
        score_result["score_greedy_parser_agreement"] = (
            score_result["candidate_score_argmax_primary"] == record["parsed_label"]
            if record["parser_status"] == "OK" else None
        )
        record.update(score_result)
    except Exception as exc:
        message = str(exc)
        oom_cls = getattr(torch.cuda, "OutOfMemoryError", RuntimeError)
        is_oom = (isinstance(exc, oom_cls) or
                  (isinstance(exc, RuntimeError) and "out of memory" in message.lower()) or
                  "cuda out of memory" in message.lower())
        failure_types = {
            "CHAT_TEMPLATE": "CHAT_TEMPLATE_FAILURE",
            "MEDIA_DECODE": "MEDIA_DECODE_FAILURE",
            "PROCESSOR": "PROCESSOR_FAILURE",
            "GENERATION": "GENERATION_FAILURE",
            "OUTPUT_DECODE": "GENERATION_DECODE_FAILURE",
            "PARSER": "PARSER_EXECUTION_FAILURE",
            "UNCERTAINTY_SCORING": "CANDIDATE_SCORING_FAILURE",
        }
        record["failure_type"] = "CUDA_OOM" if is_oom else failure_types.get(stage, "TECHNICAL_FAILURE")
        record["failure_message"] = message
        record["failure_traceback"] = traceback.format_exc()
        record["gpu_memory_after_generation_or_error"] = gpu_memory_snapshot(torch)
        if is_oom:
            counters["cuda_oom_count"] += 1
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
        else:
            counters["other_technical_failure_count"] += 1
        if stage == "PARSER":
            counters["parser_execution_failure_count"] += 1
    finally:
        inputs = generated_ids = trimmed_ids = decoded = None
        audios = images = videos = messages = None
        gc.collect()
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass
        record["gpu_memory_after_cleanup"] = gpu_memory_snapshot(torch)
        record["runtime_seconds"] = round(time.perf_counter() - started, 6)
    return record

def environment_record(torch):
    packages = {}
    for package in ("torch", "transformers", "qwen-omni-utils", "flash-attn"):
        try:
            packages[package] = importlib_metadata.version(package)
        except importlib_metadata.PackageNotFoundError:
            packages[package] = None
    gpu = None
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        gpu = {"name": props.name, "total_memory_bytes": int(total_bytes),
               "free_memory_bytes_before_model": int(free_bytes),
               "device_count": int(torch.cuda.device_count())}
    nvidia_smi = shutil.which("nvidia-smi")
    driver = None
    if nvidia_smi:
        result = subprocess.run([nvidia_smi, "--query-gpu=driver_version", "--format=csv,noheader"],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            driver = result.stdout.strip().splitlines()[0]
    return {
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "packages": packages,
        "cuda_version": torch.version.cuda,
        "cuda_driver_version": driver,
        "gpu": gpu,
        "omp_num_threads_original": OMP_ORIGINAL,
        "omp_num_threads_effective": OMP_EFFECTIVE,
        "omp_num_threads_overridden": OMP_OVERRIDDEN,
    }

def model_identity():
    config_path = MODEL_DIR / "config.json"
    index_path = MODEL_DIR / "model.safetensors.index.json"
    shards = sorted(MODEL_DIR.glob("model-*.safetensors"))
    return {
        "model_path": str(MODEL_DIR),
        "config_model_type": read_json(config_path).get("model_type") if config_path.is_file() else None,
        "config_sha256": sha256_file(config_path) if config_path.is_file() else None,
        "safetensors_index_sha256": sha256_file(index_path) if index_path.is_file() else None,
        "checkpoint_shards": [{"name": p.name, "size_bytes": p.stat().st_size} for p in shards],
    }

def report_markdown(report):
    lines = [
        "# EmotionTalk Phase 1 Competence Technical Gate V1.2",
        "",
        "Gate status: " + str(report.get("EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2_STATUS")),
        "Planned records: " + str(report.get("planned_records")),
        "Attempted records: " + str(report.get("attempted_records")),
        "Generation attempts: " + str(report.get("generation_attempt_count")),
        "Generation successes: " + str(report.get("generation_success_count")),
        "Parser executions: " + str(report.get("parser_execution_count")),
        "Parse OK / PARSE_FAIL: " + str(report.get("parse_successes")) + " / " + str(report.get("parse_failures")),
        "",
        "## Technical coverage",
    ]
    for arm, stats in report.get("technical_success_by_arm", {}).items():
        lines.append(f"- {arm}: {stats['success']} / {stats['planned']} technical successes")
    for tier, stats in report.get("tier_coverage", {}).items():
        lines.append(f"- {tier}: {stats['generation_successes']} / 3 generation successes")
    lines.extend([
        "",
        "Silent-video contract: " + str(report.get("silent_video_contract_status")),
        "Frozen hashes: " + ("PASS" if report.get("frozen_hashes_verified") else "FAIL"),
        "CUDA OOM: " + str(report.get("cuda_oom_count")),
        "Other technical failures: " + str(report.get("other_technical_failure_count")),
        "Scientific metrics computed: FALSE",
        "Science status: NOT_RUN",
        "Next step: " + str(report.get("next_step")),
        "",
        "This gate reports technical execution and parsing only. It does not compute correctness, readability, accuracy, or modality comparisons.",
        "",
    ])
    return "\n".join(lines)

remap_namespace(globals())
