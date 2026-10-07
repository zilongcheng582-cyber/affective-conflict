from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate


import argparse

import csv

import hashlib

import importlib.util

import json

import os

import subprocess

import sys

import time

import traceback

from datetime import datetime, timezone

from pathlib import Path

ROOT = project_root()

AUDIT = ROOT / "audit/EMOTIONTALK_CONTROLLED_V1"

OUT = AUDIT / "phase3_trimodal_v1"

CODE = ROOT / "code"

PAIRWISE_FREEZE = AUDIT / "phase2_scientific_analysis_v1/EMOTIONTALK_PHASE2_PAIRWISE_MODEL_FREEZE_V1.json"

PHASE2_JSONL = AUDIT / "phase2_pairwise_full_v1_attempt_002/emotiontalk_phase2_pairwise_full_v1_attempt_002.jsonl"

COMPOSITION_RULE = OUT / "EMOTIONTALK_PHASE3_COMPOSITION_RULE_FREEZE_V1.json"

PRIMARY_PLAN = OUT / "EMOTIONTALK_PHASE3_PRIMARY_PLAN_V1.csv"

GATE_SELECTION = OUT / "EMOTIONTALK_PHASE3_GATE_SELECTION_V1.csv"

PREFLIGHT = OUT / "EMOTIONTALK_PHASE3_CPU_PREFLIGHT_V1.json"

PROMPT = CODE / "prompts/emotiontalk_controlled_prompt_v1.json"

PARSER = CODE / "benchmarks/emotiontalk_controlled_parser_v1.py"

MEDIA_MANIFEST = AUDIT / "media_freeze_v1/EMOTIONTALK_MEDIA_MANIFEST_V1.csv"

CANDIDATES = AUDIT / "EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json"

MODEL_DIR = ROOT / "models/Qwen2.5-Omni-7B"

GPU_GATE_REPORT = OUT / "EMOTIONTALK_PHASE3_GPU_GATE_V1_ATTEMPT_003_REPORT.json"

GPU_GATE_PROVENANCE = OUT / "EMOTIONTALK_PHASE3_GPU_GATE_V1_ATTEMPT_003_PROVENANCE.json"

GPU_GATE_OUTPUT = OUT / "emotiontalk_phase3_gate_v1_attempt_003.jsonl"

GPU_GATE_REPORT_SHA256 = "27322644b099edbc4045102796a6e1d661a1af28ab9831961aa3681f457f3a7f"

GPU_GATE_PROVENANCE_SHA256 = "bae6cb82367f9778fcf5c8cdd1c5554341903b48e8107a7b6a00db94fc82c727"

GPU_GATE_OUTPUT_SHA256 = "2528969c7b93262a4ed8f8f1224f7b55ad3c2eb027414885d138a558257e7999"

LOCKS = {
    PAIRWISE_FREEZE: "2f5e5e639ce22d79452aa54ca599fd0e14bc525cf874042b04065edadeed5019",
    PHASE2_JSONL: "677f96d9cd8650c08486bedde14457d62a2e930d3c0b7560983d6d1c456b1381",
    COMPOSITION_RULE: "fe1623e42402d32f2ebebda8c5d8b1feaad69a852a0391e7ad2c2030dfd4d3b6",
    PRIMARY_PLAN: "14fdc30700bbdebdf97f9bc21e15a98f07e48a00038c8976579431d5163e00ab",
    GATE_SELECTION: "6658998d788965f4f80eabae305989469431fe79755e2f9cb3d785dec2120460",
    PROMPT: "ba6b71f080ea186a1494a54a0990a5740fc0aea69f008622618102f39efe55f8",
    PARSER: "c852f18279dd0d89fc8a97bab0516943775580a1a7dbcfe276e901d14ff7d374",
    MEDIA_MANIFEST: "c0343ac1cf79038dc5b9cfaf2cdebe9da3fbf13a18c24960656e2fabbd438c9d",
    CANDIDATES: "b249c68e92fa16ec7c41f617baffd1d293db8807b01b9c0f5d8490d41b790750",
}

ONTOLOGY = ("angry", "disgusted", "fearful", "happy", "neutral", "sad", "surprised")

TRI_ORDERS = (
    "A_THEN_T_THEN_V", "A_THEN_V_THEN_T", "T_THEN_A_THEN_V",
    "T_THEN_V_THEN_A", "V_THEN_A_THEN_T", "V_THEN_T_THEN_A",
)

def now():
    return datetime.now(timezone.utc).isoformat()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return relocate(list(csv.DictReader(f)))

def load_parser():
    spec = importlib.util.spec_from_file_location("emotiontalk_phase3_frozen_parser", PARSER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_label

def probe_silent_video(path: Path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=60,
    )
    streams = json.loads(p.stdout).get("streams", [])
    n_video = sum(s.get("codec_type") == "video" for s in streams)
    n_audio = sum(s.get("codec_type") == "audio" for s in streams)
    if n_video < 1 or n_audio != 0:
        raise RuntimeError("silent-video stream contract changed: " + str(path))
    return {"video_stream_count": n_video, "audio_stream_count": n_audio}

def prediction_input(row):
    # Deliberately excludes pairwise outcomes and composition prediction from prompt/generation inputs.
    keys = (
        "utterance_id", "speaker_id", "trimodal_pattern", "y_A", "y_T", "y_V",
        "majority_label", "minority_label", "audio_path", "text_path", "silent_video_path",
        "candidate_sequence_id", "candidate_sequence", "tri_order",
    )
    return {k: row[k] for k in keys}

def build_messages(row, prompt_cfg):
    tri_order = row["tri_order"]
    valid_tri_orders = set(TRI_ORDERS)
    if tri_order not in valid_tri_orders:
        raise RuntimeError(f"invalid frozen tri-order: {tri_order}")
    order = tri_order.split("_THEN_")
    if len(order) != 3 or set(order) != {"A", "T", "V"}:
        raise RuntimeError(f"invalid frozen tri-order modalities: {tri_order}")
    if "_THEN_".join(order) != tri_order:
        raise RuntimeError(f"tri-order round-trip failed: {tri_order}")
    text_obj = json.loads(Path(row["text_path"]).read_text(encoding="utf-8"))
    text = text_obj.get("content")
    if not isinstance(text, str):
        raise RuntimeError("official Text.content is not a string")
    labels = row["candidate_sequence"].split("|")
    instruction = prompt_cfg["instruction_template"].format(candidate_labels=", ".join(labels))
    content = []
    for modality in order:
        if modality == "A":
            content.append({"type": "audio", "audio": row["audio_path"]})
        elif modality == "T":
            content.append({"type": "text", "text": "Text evidence:\n" + text})
        elif modality == "V":
            content.append({"type": "video", "video": row["silent_video_path"]})
    content.append({"type": "text", "text": instruction})
    return [{"role": "user", "content": content}], order

def normalize_rendered(value):
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 1 and isinstance(value[0], str):
        return value[0]
    raise TypeError("unexpected apply_chat_template result: " + type(value).__name__)

def load_executor():
    import torch
    from qwen_omni_utils import process_mm_info
    from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
    processor = Qwen2_5OmniProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        str(MODEL_DIR), torch_dtype="auto", device_map="cuda",
        attn_implementation="flash_attention_2", local_files_only=True,
    )
    model.eval()
    return torch, process_mm_info, processor, model

def run_records(mode, rows, prompt_cfg, process_mm_info, processor, model, parse_label):
    if mode == "gate":
        out_jsonl = OUT / "emotiontalk_phase3_gate_v1_attempt_003.jsonl"
        out_report = OUT / "EMOTIONTALK_PHASE3_GPU_GATE_V1_ATTEMPT_003_REPORT.json"
    else:
        out_jsonl = OUT / ("emotiontalk_phase3_" + mode + "_v1.jsonl")
        out_report = OUT / ("EMOTIONTALK_PHASE3_" + mode.upper() + "_V1_REPORT.json")
    seen = set()
    attempted = generation_success = parser_success = 0
    start = time.time()
    with out_jsonl.open("w", encoding="utf-8") as f:
        for i, row in enumerate(rows, 1):
            key = (row["utterance_id"], row["tri_order"])
            if key in seen:
                raise RuntimeError("duplicate primary key: " + repr(key))
            seen.add(key)
            record = {
                **row, "primary_key": {"utterance_id": key[0], "tri_order": key[1]},
                "actual_evidence_order": row["tri_order"].split("_THEN_"),
                "generation_attempted": False, "generation_success": False,
                "parser_execution": False, "parser_status": None, "parsed_label": None,
                "raw_generation": None, "observed_outcome_class": None,
                "failure_type": None, "failure_message": None,
            }
            attempted += 1
            try:
                video_path = Path(row["silent_video_path"])
                if not Path(row["audio_path"]).is_file() or Path(row["audio_path"]).stat().st_size == 0:
                    raise RuntimeError("standalone audio missing/empty")
                if not Path(row["text_path"]).is_file():
                    raise RuntimeError("official text source missing")
                if not video_path.is_file() or video_path.stat().st_size == 0:
                    raise RuntimeError("silent video missing/empty")
                probe_silent_video(video_path)
                messages, order = build_messages(row, prompt_cfg)
                content_order = [x["type"] for x in messages[0]["content"][:-1]]
                expected_types = [{"A": "audio", "T": "text", "V": "video"}[m] for m in order]
                if content_order != expected_types or messages[0]["content"][-1]["type"] != "text":
                    raise RuntimeError("message evidence/instruction order mismatch")
                rendered = normalize_rendered(processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True))
                audios, images, videos = process_mm_info(messages, use_audio_in_video=False)
                if not audios or not videos:
                    raise RuntimeError("tri-modal audio/video payload missing")
                batch = processor(
                    text=rendered, audio=audios, images=images, videos=videos,
                    return_tensors="pt", padding=True, use_audio_in_video=False,
                )
                batch = batch.to(model.device).to(model.dtype)
                record["generation_attempted"] = True
                generated = model.generate(
                    **batch, do_sample=False, max_new_tokens=16,
                    use_audio_in_video=False, return_audio=False,
                )
                new_tokens = generated[:, batch["input_ids"].shape[1]:]
                raw = processor.batch_decode(
                    new_tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )[0]
                record["generation_success"] = True
                record["raw_generation"] = raw
                parsed = parse_label(raw)
                record["parser_execution"] = True
                record["parser_status"] = parsed.get("parser_status")
                record["parsed_label"] = parsed.get("parsed_label")
                label = record["parsed_label"]
                if record["parser_status"] != "OK":
                    record["observed_outcome_class"] = "PARSE_FAIL"
                    record["failure_type"] = "PARSE_FAIL"
                elif label == row["majority_label"]:
                    record["observed_outcome_class"] = "MAJORITY_LABEL"
                elif label == row["minority_label"]:
                    record["observed_outcome_class"] = "MINORITY_LABEL"
                else:
                    record["observed_outcome_class"] = "OTHER"
                parser_success += record["parser_status"] == "OK"
                f.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
                if i == 1 and not record["generation_success"]:
                    raise RuntimeError("first-record fail-fast")
            except Exception as e:
                record["failure_type"] = record["failure_type"] or "TECHNICAL_FAILURE"
                record["failure_message"] = repr(e)
                f.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
                raise RuntimeError("fail-fast at record %d %s" % (i, key)) from e
            generation_success += record["generation_success"]
            if i == 1 and not record["generation_success"]:
                raise RuntimeError("first-record fail-fast")
    if generation_success == 0:
        raise RuntimeError("generation_success=0 cannot return success")
    report = {
        "status": "COMPLETE", "mode": mode, "planned": len(rows), "attempted": attempted,
        "generation_success": generation_success, "parser_execution": parser_success,
        "unique_primary_keys": len(seen), "technical_missing": attempted-generation_success,
        "runtime_seconds": time.time()-start, "created_utc": now(),
        "output_jsonl_sha256": sha256(out_jsonl),
        "frozen_locks": {str(p): sha256(p) for p in LOCKS},
        "model_generate_called": True,
    }
    out_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

remap_namespace(globals())
