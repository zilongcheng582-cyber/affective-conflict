from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate


import argparse

import csv

import datetime as dt

import hashlib

import importlib.util

import inspect

import json

import math

import os

import statistics

import subprocess

import sys

import time

import traceback

from pathlib import Path

ROOT = project_root()

BASE = ROOT / "audit/EMOTIONTALK_CONTROLLED_V1"

FREEZE_V12 = BASE / "pre_full_measurement_freeze_v1_2"

OUT = BASE / "phase1_competence_full_v1_2"

RUNNER_SOURCE = ROOT / "code/run_qwen25_emotiontalk_phase1_v1_2.py"

RUNNER_REVISION = ROOT / "code/run_qwen25_emotiontalk_phase1_full_v1_2_r1.py"

JSONL = OUT / "emotiontalk_phase1_competence_full_v1_2.jsonl"

REPORT_JSON = OUT / "EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2.json"

REPORT_MD = OUT / "EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2.md"

PROVENANCE = OUT / "EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2_PROVENANCE.json"

PRECHECK = OUT / "EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2_PREFLIGHT.json"

PATTERNS = ("ALL_SAME", "T=A!=V", "T=V!=A", "A=V!=T", "ALL_DIFFERENT")

ARMS = ("T_ONLY", "A_ONLY", "V_ONLY")

MODS = ("T", "A", "V")

ARM_TO_MOD = {"T_ONLY": "T", "A_ONLY": "A", "V_ONLY": "V"}

READABLE_KEY = {"T": "Readable_T", "A": "Readable_A", "V": "Readable_V"}

PAIR_DEFS = {
    "AT": ("A", "T", "at_relation"),
    "AV": ("A", "V", "av_relation"),
    "VT": ("V", "T", "vt_relation"),
}

LABEL_FIELD = {"T": "text_emotion", "A": "audio_emotion", "V": "video_emotion"}

EXPECTED_FROZEN_MANIFEST_SHA = "e8e550a9587fd891fd94cac6cfef5210befa4e203accbe1d01352b5472f469fe"

EXPECTED_COMMIT = "cb8397e226ce7c1fccee41ea21161a3f98f578e1"

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def stable_digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()

def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, path)

def load_jsonl(path):
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except Exception as e:
                raise RuntimeError(f"corrupt JSONL at line {number}; preserve and review: {e}") from e
    return records

def build_samples(runner, context):
    panel = runner.read_csv(runner.PANEL_CSV)
    manifest = runner.read_csv(runner.MEDIA_MANIFEST)
    if len(panel) != 1500 or len({r["utterance_id"] for r in panel}) != 1500:
        raise RuntimeError("frozen master panel must contain exactly 1500 unique utterances")
    if len(manifest) != 1500 or len({r["utterance_id"] for r in manifest}) != 1500:
        raise RuntimeError("media manifest must contain exactly 1500 unique panel utterances")
    manifest_by_id = {r["utterance_id"]: r for r in manifest}
    uids = [r["utterance_id"] for r in panel]
    text_paths = runner.find_text_jsons(uids)
    if set(text_paths) != set(uids):
        raise RuntimeError(f"official Text JSON mapping incomplete: {len(text_paths)}/1500")
    freeze_prov = runner.read_json(runner.FREEZE_PROVENANCE)
    frozen_video_hashes = freeze_prov.get("all_derived_file_sha256", {})
    if not isinstance(frozen_video_hashes, dict):
        raise RuntimeError("media freeze provenance has no all-derived-file hash map")
    patterns = {p: 0 for p in PATTERNS}
    pairs = {p: {"conflict": 0, "consistent": 0} for p in ("AV", "AT", "VT")}
    samples = []
    for index, row in enumerate(panel, 1):
        uid = row["utterance_id"]
        if row["trimodal_pattern"] not in patterns:
            raise RuntimeError(f"unexpected frozen tri-modal pattern at {uid}")
        patterns[row["trimodal_pattern"]] += 1
        for pair, (left, right, relation_field) in PAIR_DEFS.items():
            relation = "conflict" if row[LABEL_FIELD[left]] != row[LABEL_FIELD[right]] else "consistent"
            if row.get(relation_field) != relation.upper():
                raise RuntimeError(f"frozen pair relation mismatch at {uid} {pair}")
            pairs[pair][relation] += 1
        mr = manifest_by_id.get(uid)
        if mr is None:
            raise RuntimeError(f"media manifest missing {uid}")
        if row["audio_path"] != mr.get("audio_path") or row["video_path"] != mr.get("source_av_video_path"):
            raise RuntimeError(f"panel/media original path mismatch for {uid}")
        if mr.get("validation_status") != "PASS" or mr.get("silent_audio_stream_count") != "0":
            raise RuntimeError(f"frozen silent-video manifest contract missing for {uid}")
        silent_path = Path(mr.get("silent_video_path", ""))
        audio_path = Path(row["audio_path"])
        if not audio_path.is_file() or audio_path.stat().st_size <= 0:
            raise RuntimeError(f"standalone audio missing/empty for {uid}: {audio_path}")
        if not silent_path.is_file() or silent_path.stat().st_size <= 0:
            raise RuntimeError(f"frozen silent video missing/empty for {uid}: {silent_path}")
        media_hash = mr.get("silent_video_sha256")
        if not media_hash or frozen_video_hashes.get(uid) != media_hash:
            raise RuntimeError(f"manifest and freeze provenance silent-video hashes differ for {uid}")
        seq = row["candidate_sequence"]
        labels = seq.split("|")
        if len(labels) != 7 or len(set(labels)) != 7 or set(labels) != set(runner.ONTOLOGY):
            raise RuntimeError(f"candidate sequence invalid for {uid}")
        official_text_path = text_paths[uid]
        text_json = runner.read_json(official_text_path)
        official_text = text_json.get("content") if isinstance(text_json, dict) else None
        if not isinstance(official_text, str) or official_text != row["text"]:
            raise RuntimeError(f"panel text differs from official Text.content for {uid}")
        sample = {
            "resource_tier": "MASTER_PANEL",
            "utterance_id": uid,
            "candidate_sequence_id": row["candidate_sequence_id"],
            "candidate_sequence": seq,
            "candidate_labels": labels,
            "text_emotion": row["text_emotion"],
            "audio_emotion": row["audio_emotion"],
            "video_emotion": row["video_emotion"],
            "text": official_text,
            "text_json_path": str(official_text_path),
            "audio_path": str(audio_path),
            "silent_video_path": str(silent_path),
            "media_manifest_video_sha256": media_hash,
            "video_stream_probe": {"video_stream_count": 1, "audio_stream_count": 0,
                                    "source": "frozen_media_manifest"},
            "speaker_id": row["speaker_id"],
            "official_split": row.get("official_split", ""),
            "multimodal_emotion": row["multimodal_emotion"],
            "trimodal_pattern": row["trimodal_pattern"],
            "frozen_panel_row_index": index,
            "video_file_size_bytes": silent_path.stat().st_size,
        }
        samples.append(sample)
    if patterns != {p: 300 for p in PATTERNS}:
        raise RuntimeError(f"frozen master panel pattern counts changed: {patterns}")
    expected_pairs = {p: {"conflict": 900, "consistent": 600} for p in pairs}
    if pairs != expected_pairs:
        raise RuntimeError(f"frozen pairwise structure changed: {pairs}")
    return samples, panel, patterns, pairs, manifest_by_id

def make_frozen_hashes(runner, context, gate, patch_sha):
    files = {
        "frozen_v1_2_manifest_sha256": gate["frozen_manifest_sha256"],
        "v1_2_source_runner_sha256": sha_file(RUNNER_SOURCE),
        "protocol_json_sha256": sha_file(runner.PROTOCOL_JSON),
        "master_panel_sha256": sha_file(runner.PANEL_CSV),
        "candidate_sequences_sha256": sha_file(runner.CANDIDATE_JSON),
        "prompt_sha256": sha_file(runner.PROMPT_PATH),
        "parser_sha256": sha_file(runner.PARSER_PATH),
        "measurement_spec_sha256": sha_file(FREEZE_V12 / "EMOTIONTALK_MEASUREMENT_SPEC_V1_2.json"),
        "compositionality_spec_sha256": sha_file(FREEZE_V12 / "EMOTIONTALK_COMPOSITIONALITY_SPEC_V1_1.json"),
        "cross_regime_transfer_spec_sha256": sha_file(FREEZE_V12 / "CROSS_REGIME_TRANSFER_SPEC_V1.json"),
        "media_manifest_sha256": sha_file(runner.MEDIA_MANIFEST),
        "media_freeze_report_sha256": sha_file(runner.FREEZE_REPORT),
        "media_freeze_provenance_sha256": sha_file(runner.FREEZE_PROVENANCE),
        "effective_perform_arm_sha256": patch_sha,
        "full_runner_revision_sha256": sha_file(RUNNER_REVISION),
    }
    files["frozen_input_bundle_sha256"] = stable_digest(files)
    return files

def append_checkpoint(path, row):
    encoded = json.dumps(row, ensure_ascii=False, allow_nan=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(encoded + "\n")
        f.flush()
        os.fsync(f.fileno())

def is_complete_record(row, bundle_sha):
    return (bool(row) and row.get("frozen_input_bundle_sha256") == bundle_sha
            and row.get("generation_success") is True
            and row.get("parser_execution") is True
            and row.get("parser_execution_success") is True
            and row.get("parser_status") in ("OK", "PARSE_FAIL")
            and row.get("candidate_scoring_status") == "OK")

def failure_category(row):
    if row.get("parser_status") == "PARSER_EXCEPTION" or row.get("failure_type") == "PARSER_EXECUTION_FAILURE":
        return "PARSER_EXCEPTION", True
    if row.get("candidate_scoring_status") == "OK":
        if row.get("parser_status") == "PARSE_FAIL":
            return "PARSE_FAIL", False
        return "", False
    if row.get("failure_type") == "CUDA_OOM":
        return "CUDA_OOM", True
    ft = str(row.get("failure_type") or "")
    mapping = {
        "MEDIA_DECODE_FAILURE": "MEDIA_FAILURE",
        "PROCESSOR_FAILURE": "PROCESSOR_FAILURE",
        "GENERATION_FAILURE": "GENERATION_FAILURE",
        "GENERATION_DECODE_FAILURE": "GENERATION_FAILURE",
        "CANDIDATE_SCORING_FAILURE": "CANDIDATE_SCORE_FAILURE",
        "CHAT_TEMPLATE_FAILURE": "PROCESSOR_FAILURE",
        "TECHNICAL_FAILURE": "UNKNOWN_TECHNICAL_FAILURE",
    }
    if ft:
        return mapping.get(ft, "UNKNOWN_TECHNICAL_FAILURE"), True
    if row.get("generation_success") and row.get("parser_status") == "PARSE_FAIL":
        return "PARSE_FAIL", False
    return "UNKNOWN_TECHNICAL_FAILURE", True

def metric_value(row, metric):
    if metric == "entropy":
        return (row.get("candidate_entropy_primary") or {}).get("normalized_by_log7")
    if metric == "margin":
        return row.get("candidate_top1_top2_margin_primary")
    if metric == "source_probability":
        return row.get("source_label_probability_primary")
    return None

def percentiles(values):
    values = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    if not values:
        return {"n": 0, "mean": None, "median": None, "p25": None, "p75": None}
    def pct(p):
        x = (len(values) - 1) * p
        lo = int(math.floor(x)); hi = int(math.ceil(x))
        return values[lo] if lo == hi else values[lo] * (hi - x) + values[hi] * (x - lo)
    return {"n": len(values), "mean": statistics.fmean(values), "median": statistics.median(values),
            "p25": pct(.25), "p75": pct(.75)}

def bool_csv(v):
    if v is None:
        return "NA"
    return "TRUE" if v else "FALSE"

def safe_readable(row):
    if row is None or not row.get("generation_success") or row.get("parser_status") != "OK":
        return None
    pred = row.get("parsed_label")
    if not pred:
        return None
    mod = ARM_TO_MOD[row["arm"]]
    return pred == row.get({"T": "text_emotion", "A": "audio_emotion", "V": "video_emotion"}[mod])

def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def summarize(runner, samples, panel_rows, records, frozen_hashes):
    latest = {}
    attempts = {}
    for row in records:
        key = (row.get("utterance_id"), row.get("arm"))
        attempts[key] = attempts.get(key, 0) + 1
        latest[key] = row
    by_uid = {s["utterance_id"]: s for s in samples}
    sample_rows = []
    for p in panel_rows:
        uid = p["utterance_id"]
        arms = {m: latest.get((uid, f"{m}_ONLY")) for m in MODS}
        readable = {m: safe_readable(arms[m]) for m in MODS}
        tech = {m: bool(arms[m] and is_complete_record(arms[m], frozen_hashes["frozen_input_bundle_sha256"])) for m in MODS}
        pair_values = {}
        for pair, (left, right, _) in PAIR_DEFS.items():
            pair_values[pair] = (readable[left] and readable[right]
                                 if tech[left] and tech[right] and readable[left] is not None and readable[right] is not None
                                 else None)
        triple = (all(readable[m] is True for m in MODS)
                  if all(tech[m] for m in MODS) and all(readable[m] is not None for m in MODS)
                  else None)
        def field(m, key, nested=False):
            r = arms[m]
            if not r:
                return None
            return (r.get(key) or {}).get("normalized_by_log7") if nested else r.get(key)
        row = {
            "utterance_id": uid, "trimodal_pattern": p["trimodal_pattern"],
            "speaker_id": p["speaker_id"], "official_split": p.get("official_split", ""),
            "y_T": p["text_emotion"], "y_A": p["audio_emotion"], "y_V": p["video_emotion"],
            "y_M": p["multimodal_emotion"], "candidate_sequence_id": p["candidate_sequence_id"],
            "candidate_sequence": p["candidate_sequence"],
            "pred_T": arms["T"].get("parsed_label") if arms["T"] else None,
            "pred_A": arms["A"].get("parsed_label") if arms["A"] else None,
            "pred_V": arms["V"].get("parsed_label") if arms["V"] else None,
            "parser_status_T": arms["T"].get("parser_status") if arms["T"] else "NOT_ATTEMPTED",
            "parser_status_A": arms["A"].get("parser_status") if arms["A"] else "NOT_ATTEMPTED",
            "parser_status_V": arms["V"].get("parser_status") if arms["V"] else "NOT_ATTEMPTED",
            "Readable_T": bool_csv(readable["T"]), "Readable_A": bool_csv(readable["A"]),
            "Readable_V": bool_csv(readable["V"]),
            "DualReadable_AT": bool_csv(pair_values["AT"]),
            "DualReadable_AV": bool_csv(pair_values["AV"]),
            "DualReadable_VT": bool_csv(pair_values["VT"]), "TripleReadable": bool_csv(triple),
            "entropy_T": field("T", "candidate_entropy_primary", True),
            "entropy_A": field("A", "candidate_entropy_primary", True),
            "entropy_V": field("V", "candidate_entropy_primary", True),
            "margin_T": field("T", "candidate_top1_top2_margin_primary"),
            "margin_A": field("A", "candidate_top1_top2_margin_primary"),
            "margin_V": field("V", "candidate_top1_top2_margin_primary"),
            "source_prob_T": field("T", "source_label_probability_primary"),
            "source_prob_A": field("A", "source_label_probability_primary"),
            "source_prob_V": field("V", "source_label_probability_primary"),
            "technical_complete_T": bool_csv(tech["T"]),
            "technical_complete_A": bool_csv(tech["A"]),
            "technical_complete_V": bool_csv(tech["V"]),
            "failure_type_T": arms["T"].get("failure_type") if arms["T"] else "NO_RECORD",
            "failure_type_A": arms["A"].get("failure_type") if arms["A"] else "NO_RECORD",
            "failure_type_V": arms["V"].get("failure_type") if arms["V"] else "NO_RECORD",
            "greedy_score_agreement_T": bool_csv(arms["T"].get("score_greedy_parser_agreement") if arms["T"] else None),
            "greedy_score_agreement_A": bool_csv(arms["A"].get("score_greedy_parser_agreement") if arms["A"] else None),
            "greedy_score_agreement_V": bool_csv(arms["V"].get("score_greedy_parser_agreement") if arms["V"] else None),
        }
        sample_rows.append(row)
    sample_csv = OUT / "EMOTIONTALK_PHASE1_SAMPLE_TABLE_V1_2.csv"
    write_csv(sample_csv, sample_rows)

    # A metric is evaluable only when every necessary arm is complete and has an OK label parse.
    metric_specs = {
        "Readable_T": ("T",), "Readable_A": ("A",), "Readable_V": ("V",),
        "DualReadable_AT": ("A", "T"), "DualReadable_AV": ("A", "V"),
        "DualReadable_VT": ("V", "T"), "TripleReadable": ("T", "A", "V"),
    }
    metric_counts = {}
    for metric, needed in metric_specs.items():
        rows = [r for r in sample_rows if all(r[f"technical_complete_{m}"] == "TRUE" and
                                             r[f"parser_status_{m}"] == "OK" for m in needed)]
        field = metric
        positives = sum(r[field] == "TRUE" for r in rows)
        metric_counts[metric] = {"numerator": positives, "denominator": len(rows),
                                 "percentage": 100.0 * positives / len(rows) if rows else None,
                                 "technical_missing_N": len(sample_rows) - sum(
                                     all(r[f"technical_complete_{m}"] == "TRUE" for m in needed) for r in sample_rows),
                                 "not_evaluable_N": len(sample_rows) - len(rows)}

    pattern_rows = []
    for pattern in PATTERNS:
        subset = [r for r in sample_rows if r["trimodal_pattern"] == pattern]
        entry = {"trimodal_pattern": pattern, "N_panel": len(subset)}
        for metric, needed in metric_specs.items():
            evaluable = [r for r in subset if all(r[f"technical_complete_{m}"] == "TRUE" and
                                                 r[f"parser_status_{m}"] == "OK" for m in needed)]
            n = sum(r[metric] == "TRUE" for r in evaluable)
            tech_missing = sum(not all(r[f"technical_complete_{m}"] == "TRUE" for m in needed) for r in subset)
            entry.update({f"{metric}_n": n, f"{metric}_denominator": len(evaluable),
                          f"{metric}_percent": 100.0 * n / len(evaluable) if evaluable else None,
                          f"{metric}_technical_missing_N": tech_missing})
        pattern_rows.append(entry)
    write_csv(OUT / "EMOTIONTALK_PHASE1_PATTERN_SUMMARY_V1_2.csv", pattern_rows)

    label_rows = []
    source_field = {"T": "y_T", "A": "y_A", "V": "y_V"}
    for m in MODS:
        for label in runner.ONTOLOGY:
            subset = [r for r in sample_rows if r[source_field[m]] == label]
            ev = [r for r in subset if r[f"technical_complete_{m}"] == "TRUE" and r[f"parser_status_{m}"] == "OK"]
            correct = sum(r[f"Readable_{m}"] == "TRUE" for r in ev)
            tech_missing = sum(r[f"technical_complete_{m}"] != "TRUE" for r in subset)
            label_rows.append({"modality": m, "source_label": label, "N_panel": len(subset),
                               "readable_n": correct, "evaluable_n": len(ev),
                               "readable_percent": 100.0 * correct / len(ev) if ev else None,
                               "technical_missing_N": tech_missing,
                               "parse_fail_N": sum(r[f"parser_status_{m}"] == "PARSE_FAIL" for r in subset)})
    write_csv(OUT / "EMOTIONTALK_PHASE1_LABEL_SUMMARY_V1_2.csv", label_rows)

    # Frozen population tuple weights are secondary complete-case estimates only.
    weighting_path = FREEZE_V12 / "EMOTIONTALK_POPULATION_WEIGHTING_SPEC_V1.json"
    weighting_spec = json.loads(weighting_path.read_text(encoding="utf-8"))
    weight_map = {}
    for item in weighting_spec.get("ordered_tuple_counts", []):
        if item.get("panel_support"):
            key = (item["text_label"], item["audio_label"], item["video_label"])
            weight_map[key] = float(item["population_to_panel_weight"])
    weighted = {}
    for metric, needed in metric_specs.items():
        mod = metric[-1] if metric.startswith("Readable_") else None
        valid = []
        for r in sample_rows:
            if not all(r[f"technical_complete_{m}"] == "TRUE" and r[f"parser_status_{m}"] == "OK" for m in needed):
                continue
            key = (r["y_T"], r["y_A"], r["y_V"])
            w = weight_map.get(key)
            if w is not None:
                valid.append((r[metric] == "TRUE", w))
        den = sum(w for _, w in valid)
        weighted[metric] = {"status": "SECONDARY", "estimate": sum(float(y) * w for y, w in valid) / den if den else None,
                            "weighted_evaluable_mass": den, "unweighted_evaluable_n": len(valid),
                            "spec": "ordered T/A/V tuple post-stratification; positive panel support only"}

    # Model uncertainty, candidate-position sensitivity, and greedy-score agreement.
    uncertainty_rows = []
    position_rows = []
    agreement = {}
    for m in MODS:
        arm = f"{m}_ONLY"
        model_records = [latest.get((s["utterance_id"], arm)) for s in samples]
        for readable_status in ("TRUE", "FALSE"):
            for metric_name, key in (("normalized_entropy", "entropy"), ("top1_top2_margin", "margin"),
                                     ("source_label_probability", "source_probability")):
                vals = []
                for r in model_records:
                    if r is None:
                        continue
                    uid = r["utterance_id"]
                    sr = next(x for x in sample_rows if x["utterance_id"] == uid)
                    if sr[f"Readable_{m}"] == readable_status:
                        vals.append(metric_value(r, key))
                stats = percentiles(vals)
                uncertainty_rows.append({"domain": "MODEL", "modality": m,
                                         "readable_status": readable_status, "metric": metric_name, **stats})
        # Candidate position diagnostic by source emotion label at positions 1..7.
        for label in runner.ONTOLOGY:
            for pos in range(1, 8):
                relevant = []
                for sample in samples:
                    if sample[{"T": "text_emotion", "A": "audio_emotion", "V": "video_emotion"}[m]] != label:
                        continue
                    if sample["candidate_labels"][pos - 1] == label:
                        r = latest.get((sample["utterance_id"], arm))
                        if r and safe_readable(r) is not None:
                            relevant.append(safe_readable(r))
                position_rows.append({"modality": m, "source_label": label, "candidate_position": pos,
                                      "readable_n": sum(relevant), "evaluable_n": len(relevant),
                                      "readable_percent": 100.0 * sum(relevant) / len(relevant) if relevant else None})
        comparisons = [r for r in model_records if r and r.get("candidate_scoring_status") == "OK"
                       and r.get("parser_status") == "OK" and r.get("score_greedy_parser_agreement") is not None]
        agreement[m] = {"agreement_n": sum(r["score_greedy_parser_agreement"] is True for r in comparisons),
                        "evaluable_n": len(comparisons),
                        "disagreement_n": sum(r["score_greedy_parser_agreement"] is False for r in comparisons)}
    write_csv(OUT / "EMOTIONTALK_PHASE1_UNCERTAINTY_SUMMARY_V1_2.csv", uncertainty_rows)
    write_csv(OUT / "EMOTIONTALK_PHASE1_CANDIDATE_POSITION_SUMMARY_V1_2.csv", position_rows)

    # Human annotation uncertainty joined to each modality's unchanged readability label.
    ann_path = FREEZE_V12 / "EMOTIONTALK_ANNOTATION_UNCERTAINTY_V1.csv"
    annotation_rows = runner.read_csv(ann_path)
    ann_map = {(r["utterance_id"], r["modality"]): r for r in annotation_rows}
    human_comparisons = {}
    for m in MODS:
        for status in ("TRUE", "FALSE"):
            joined = []
            for sr in sample_rows:
                if sr[f"Readable_{m}"] != status:
                    continue
                ar = ann_map.get((sr["utterance_id"], m))
                if ar:
                    joined.append(ar)
            for col in ("confidence_degree_mean", "vote_entropy_normalized_by_log7", "source_label_vote_fraction"):
                vals = []
                for ar in joined:
                    try:
                        vals.append(float(ar[col]))
                    except (TypeError, ValueError):
                        pass
                st = percentiles(vals)
                uncertainty_rows.append({"domain": "ANNOTATOR", "modality": m,
                                         "readable_status": status, "metric": col, **st})
            human_comparisons.setdefault(m, {})[status] = {
                "n": len(joined),
                "confidence_degree_mean": percentiles([float(a["confidence_degree_mean"]) for a in joined if a.get("confidence_degree_mean")])["mean"],
                "vote_entropy_normalized_mean": percentiles([float(a["vote_entropy_normalized_by_log7"]) for a in joined if a.get("vote_entropy_normalized_by_log7")])["mean"],
            }
    write_csv(OUT / "EMOTIONTALK_PHASE1_UNCERTAINTY_SUMMARY_V1_2.csv", uncertainty_rows)

    # Future execution populations only; no pairwise or tri-modal generations here.
    pair_plan = {"status": "PLANNING_ONLY_NOT_RUN", "pairs": {}, "planned_phase2_joint_generations": 0}
    for pair, (left, right, _) in PAIR_DEFS.items():
        conflict = consistent = 0
        conflict_ids, consistent_ids = [], []
        for p, sr in zip(panel_rows, sample_rows):
            dual = sr[f"DualReadable_{pair}"] == "TRUE"
            is_conflict = p[LABEL_FIELD[left]] != p[LABEL_FIELD[right]]
            if dual and is_conflict:
                conflict += 1; conflict_ids.append(p["utterance_id"])
            elif dual and not is_conflict:
                consistent += 1; consistent_ids.append(p["utterance_id"])
        dual_n = conflict + consistent
        pair_plan["pairs"][pair] = {"dual_readable_total": dual_n,
                                     "conflict_and_dual_readable_N": conflict,
                                     "consistent_and_dual_readable_N": consistent,
                                     "conflict_utterance_ids": conflict_ids,
                                     "consistent_utterance_ids": consistent_ids,
                                     "planned_joint_generations": 2 * dual_n}
        pair_plan["planned_phase2_joint_generations"] += 2 * dual_n
    pair_plan["model_inference_run"] = False
    atomic_json(OUT / "EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json", pair_plan)

    phase3 = {"status": "PLANNING_ONLY_NOT_RUN", "patterns": {}, "triple_readable_non_all_same_N": 0,
              "planned_phase3_generations": 0, "model_inference_run": False}
    for pat in PATTERNS:
        n = sum(r["trimodal_pattern"] == pat and r["TripleReadable"] == "TRUE" for r in sample_rows)
        phase3["patterns"][pat] = {"triple_readable_N": n}
        if pat != "ALL_SAME":
            phase3["triple_readable_non_all_same_N"] += n
    phase3["planned_phase3_generations"] = 6 * phase3["triple_readable_non_all_same_N"]
    atomic_json(OUT / "EMOTIONTALK_PHASE3_POPULATION_PLAN_V1_2.json", phase3)

    failures = []
    for key, r in latest.items():
        cat, technical = failure_category(r)
        if cat:
            s = by_uid.get(r.get("utterance_id"), {})
            failures.append({"utterance_id": r.get("utterance_id"), "arm": r.get("arm"),
                             "panel_row_index": s.get("frozen_panel_row_index"),
                             "failure_category": cat, "is_technical_failure": technical,
                             "failure_type": r.get("failure_type"), "failure_message": r.get("failure_message"),
                             "parser_failure_message": r.get("parser_failure_message"),
                             "candidate_scoring_status": r.get("candidate_scoring_status"),
                             "video_path": r.get("silent_video_path") if r.get("arm") == "V_ONLY" else None,
                             "video_file_size_bytes": s.get("video_file_size_bytes") if r.get("arm") == "V_ONLY" else None,
                             "video_processing_metadata": json.dumps(r.get("video_processing_metadata"), ensure_ascii=False),
                             "gpu_memory_before": json.dumps(r.get("gpu_memory_before"), ensure_ascii=False),
                             "gpu_memory_after_generation_or_error": json.dumps(r.get("gpu_memory_after_generation_or_error"), ensure_ascii=False),
                             "gpu_memory_after_cleanup": json.dumps(r.get("gpu_memory_after_cleanup"), ensure_ascii=False),
                             "failure_traceback": r.get("failure_traceback") or r.get("parser_failure_traceback")})
    write_csv(OUT / "EMOTIONTALK_PHASE1_TECHNICAL_FAILURES_V1_2.csv", failures)

    technical_missing = sum(not is_complete_record(latest.get((s["utterance_id"], arm)), frozen_hashes["frozen_input_bundle_sha256"])
                            for s in samples for arm in ARMS)
    records_attempted = sum((s["utterance_id"], arm) in latest for s in samples for arm in ARMS)
    generation_success = sum(bool(latest.get((s["utterance_id"], arm), {}).get("generation_success")) for s in samples for arm in ARMS)
    parser_exec = sum(bool(latest.get((s["utterance_id"], arm), {}).get("parser_execution")) for s in samples for arm in ARMS)
    score_success = sum(latest.get((s["utterance_id"], arm), {}).get("candidate_scoring_status") == "OK" for s in samples for arm in ARMS)
    parse_fails = {m: sum(latest.get((s["utterance_id"], f"{m}_ONLY"), {}).get("parser_status") == "PARSE_FAIL" for s in samples)
                   for m in MODS}
    total_generation_attempts = sum(bool(r.get("generation_attempted")) for r in records)
    total_candidate_scores = sum(r.get("candidate_scoring_status") == "OK" for r in records)
    total_oom = sum(r.get("failure_type") == "CUDA_OOM" for r in records)
    full_slots = records_attempted == 4500
    if full_slots and technical_missing == 0:
        status = "COMPLETE"
    elif full_slots:
        status = "COMPLETE_WITH_TECHNICAL_MISSINGNESS"
    else:
        status = "TECHNICAL_FAILURE"
    panel_splits = {}
    for p in panel_rows:
        panel_splits[p.get("official_split", "unknown")] = panel_splits.get(p.get("official_split", "unknown"), 0) + 1
    report = {
        "EMOTIONTALK_PHASE1_COMPETENCE_FULL_RUN_V1_2_STATUS": status,
        "EMOTIONTALK_PHASE1_COMPETENCE_STATUS": status if status.startswith("COMPLETE") else "INCOMPLETE",
        "EMOTIONTALK_PAIRWISE_SCIENCE_STATUS": "NOT_RUN",
        "EMOTIONTALK_TRIMODAL_SCIENCE_STATUS": "NOT_RUN",
        "EMOTIONTALK_CROSS_REGIME_TRANSFER_STATUS": "NOT_RUN",
        "planned_records": 4500, "unique_record_slots_attempted": records_attempted,
        "attempted_records": records_attempted, "generation_attempts_all_attempts": total_generation_attempts,
        "generation_success_latest_record_per_slot": generation_success,
        "parser_execution_latest_record_per_slot": parser_exec,
        "candidate_score_success_latest_record_per_slot": score_success,
        "candidate_score_success_all_attempts": total_candidate_scores,
        "technical_missing_latest_record_per_slot": technical_missing,
        "parse_failures_by_modality": parse_fails,
        "cuda_oom_all_attempts": total_oom,
        "other_technical_failure_N": len([f for f in failures if f["is_technical_failure"] and f["failure_category"] != "CUDA_OOM"]),
        "readability": metric_counts,
        "readability_secondary_natural_distribution_weighted": weighted,
        "pattern_summary": pattern_rows,
        "label_summary": label_rows,
        "uncertainty_summary_csv": "EMOTIONTALK_PHASE1_UNCERTAINTY_SUMMARY_V1_2.csv",
        "candidate_position_sensitivity_csv": "EMOTIONTALK_PHASE1_CANDIDATE_POSITION_SUMMARY_V1_2.csv",
        "greedy_vs_score_argmax_agreement": agreement,
        "human_annotation_uncertainty_by_readability": human_comparisons,
        "phase2_population_plan": pair_plan,
        "phase3_population_plan": phase3,
        "panel_split_composition_descriptive_only": panel_splits,
        "model_inference_run": True,
        "pairwise_joint_inference_run": False,
        "trimodal_inference_run": False,
        "compositionality_evaluation_run": False,
        "cross_regime_transfer_fitting_run": False,
        "media_modified": False,
        "next_step": "EMOTIONTALK_PHASE2_PAIRWISE_TECHNICAL_GATE" if status.startswith("COMPLETE") else "RESUME_OR_STOP_FOR_REVIEW",
        "execution_timestamp_utc": utc_now(),
    }
    atomic_json(REPORT_JSON, report)
    md = render_markdown(report)
    REPORT_MD.write_text(md, encoding="utf-8")
    return report

def render_markdown(r):
    lines = [
        "# EmotionTalk Phase 1 Competence Full Run V1.2", "",
        f"Status: **{r['EMOTIONTALK_PHASE1_COMPETENCE_FULL_RUN_V1_2_STATUS']}**", "",
        "## Coverage", "",
        f"- Planned: {r['planned_records']}",
        f"- Attempted unique slots: {r['attempted_records']}",
        f"- Generation successes (latest per slot): {r['generation_success_latest_record_per_slot']}",
        f"- Parser executions (latest per slot): {r['parser_execution_latest_record_per_slot']}",
        f"- Candidate-score successes (latest per slot): {r['candidate_score_success_latest_record_per_slot']}",
        f"- Technical missing: {r['technical_missing_latest_record_per_slot']}",
        f"- Parse failures (T/A/V): {r['parse_failures_by_modality']}",
        f"- CUDA OOM across attempts: {r['cuda_oom_all_attempts']}", "",
        "## Readability", "",
    ]
    for metric, value in r["readability"].items():
        lines.append(f"- {metric}: {value['numerator']} / {value['denominator']} ({value['percentage']}%); technical missing N={value['technical_missing_N']}; not evaluable N={value['not_evaluable_N']}")
    lines += ["", "## Pairwise future populations (accounting only)", ""]
    for pair, vals in r["phase2_population_plan"]["pairs"].items():
        lines.append(f"- {pair}: conflict + DualReadable={vals['conflict_and_dual_readable_N']}; consistent + DualReadable={vals['consistent_and_dual_readable_N']}; planned generations={vals['planned_joint_generations']}")
    lines += ["", "## Tri-modal future population (accounting only)", "",
              f"- TripleReadable and not ALL_SAME: {r['phase3_population_plan']['triple_readable_non_all_same_N']}",
              f"- Planned Phase 3 generations: {r['phase3_population_plan']['planned_phase3_generations']}", "",
              "## Frozen scope", "",
              "Phase 2 pairwise joint inference, tri-modal inference, compositionality evaluation, transfer fitting, prompt/parser tuning, panel reselection, and media changes were not run.", "",
              "Next step: `" + r["next_step"] + "`", ""]
    return "\n".join(lines)

def attempts_for_key(records, uid, arm):
    return sum(r.get("utterance_id") == uid and r.get("arm") == arm for r in records)

from src.emotiontalk.phase1 import execution as runner

remap_namespace(globals())
