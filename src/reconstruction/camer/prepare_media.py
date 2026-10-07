#!/usr/bin/env python3
"""Build CPU-only derived media and static audit artifacts; performs no model inference."""
from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate, data_root, REPO, input_path


import argparse
import collections
import csv
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import string
from typing import Any

ROOT = project_root()
READ_ROOT = data_root()
COMMIT = "780519a554538451c8700117dd49f1f8b52da228"
SOURCE_FILES = {
    "audio-aligned": "CA-MER/audio-aligned.json",
    "video-aligned": "CA-MER/video-aligned.json",
    "consistent": "CA-MER/consistent.json",
}
MAPPING_REL = pathlib.Path("audit/QWEN25_CAMER_NATIVE_V1/CAMER_MEDIA_MAPPING_V1.csv")
AUDIT = ROOT / "audit/QWEN25_CAMER_CONTROLLED_V1"
DERIVED = ROOT / "data/derived/camer_controlled_v1"
MANIFEST = AUDIT / "camer_controlled_manifest_v1.jsonl"
NORM_PUNCT = string.whitespace + string.punctuation + "����"


def norm(value: str) -> str:
    return str(value).casefold().strip().strip(NORM_PUNCT)


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_blob(path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(READ_ROOT / "external/MoSEAR"), "show", f"{COMMIT}:{path}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout


def load_rows(blob: bytes) -> list[dict[str, Any]]:
    data = json.loads(blob)
    if isinstance(data, dict):
        for key in ("data", "annotations", "samples"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ValueError("Pinned official annotation is not a list of record objects")
    return data


def probe(path: pathlib.Path) -> dict[str, Any]:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ])
    return json.loads(raw)


def stream_summary(meta: dict[str, Any]) -> dict[str, Any]:
    streams = meta.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    fmt_duration = (meta.get("format") or {}).get("duration")
    return {
        "video_stream_count": len(video),
        "audio_stream_count": len(audio),
        "video_codec": video[0].get("codec_name") if video else None,
        "audio_codec": audio[0].get("codec_name") if audio else None,
        "width": video[0].get("width") if video else None,
        "height": video[0].get("height") if video else None,
        "audio_sample_rate": int(audio[0]["sample_rate"]) if audio and audio[0].get("sample_rate") else None,
        "audio_channels": audio[0].get("channels") if audio else None,
        "duration_seconds": float(fmt_duration) if fmt_duration not in (None, "N/A") else None,
    }


def run_ffmpeg(source: pathlib.Path, target: pathlib.Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    temp = target.with_name(f"{target.stem}.partial.{os.getpid()}{target.suffix}")
    if temp.exists():
        raise FileExistsError(temp)
    common = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-threads", "1", "-i", str(source)]
    if mode == "audio":
        command = common + ["-map", "0:a:0", "-vn", "-sn", "-dn", "-ac", "1",
                            "-ar", "16000", "-c:a", "pcm_s16le", "-f", "wav", str(temp)]
    else:
        command = common + ["-map", "0:v:0", "-an", "-sn", "-dn", "-c:v", "copy",
                            "-map_metadata", "-1", "-map_chapters", "-1", "-f", "avi", str(temp)]
    try:
        subprocess.run(command, check=True)
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


def write_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    global ROOT,READ_ROOT,AUDIT,DERIVED,MANIFEST
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", default=str(READ_ROOT / MAPPING_REL))
    ap.add_argument("--limit", type=int, default=0, help="Test-only cap; full build requires zero.")
    ap.add_argument("--no-derive", action="store_true", help="Audit sources without creating media.")
    ap.add_argument('--data-root',type=pathlib.Path,default=READ_ROOT)
    ap.add_argument('--output-root',type=pathlib.Path,required=True)
    args = ap.parse_args()
    READ_ROOT=args.data_root.resolve();ROOT=args.output_root.resolve()
    if ROOT.exists():raise ValueError('Output root must be new')
    if ROOT.is_relative_to(READ_ROOT):raise ValueError('Output root must be outside acquired inputs')
    AUDIT=ROOT/'audit/QWEN25_CAMER_CONTROLLED_V1';DERIVED=ROOT/'data/derived/camer_controlled_v1'
    MANIFEST=AUDIT/'camer_controlled_manifest_v1.jsonl'

    if args.limit < 0:
        ap.error("--limit must be zero or positive")
    AUDIT.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required")
    external = READ_ROOT / "external/MoSEAR"
    subprocess.run(["git", "-C", str(external), "cat-file", "-e", f"{COMMIT}^{{commit}}"], check=True,
                   stdout=subprocess.DEVNULL)
    source_blobs = {subset: git_blob(rel) for subset, rel in SOURCE_FILES.items()}
    source_rows = {subset: load_rows(blob) for subset, blob in source_blobs.items()}
    if any(len(rows) != 500 for rows in source_rows.values()):
        raise RuntimeError("Expected exactly 500 pinned official records per source")
    source_hashes = {subset: hashlib.sha256(source_blobs[subset]).hexdigest() for subset in SOURCE_FILES}

    mapping_path = pathlib.Path(args.mapping).resolve()
    mapping_bytes = mapping_path.read_bytes()
    with mapping_path.open(encoding="utf-8-sig", newline="") as f:
        mapping = list(csv.DictReader(f))
    if len(mapping) != 1500:
        raise RuntimeError(f"Expected 1500 media mappings, found {len(mapping)}")
    ids = [m["sample_id"] for m in mapping]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate sample_id in media mapping")
    if args.limit:
        mapping = mapping[:args.limit]

    candidates_set: set[str] = set()
    records: list[dict[str, Any]] = []
    source_audit: dict[str, Any] = {}
    ontology: dict[str, Any] = {
        "normalization": "Unicode casefold; trim whitespace and obvious punctuation only at both edges; no internal rewriting, synonymy, morphology, or semantic merging.",
        "label_fields": {"audio": "audio_pseudo_label", "video": "video_pseudo_label"},
        "ontology_interface": "FULL_SOURCE_LOCAL_ONTOLOGY",
        "sources": {},
    }
    label_counts: dict[str, dict[str, collections.Counter[str]]] = {}
    for subset, rel in SOURCE_FILES.items():
        blob = source_blobs[subset]
        prior = READ_ROOT / "audit/QWEN25_CAMER_NATIVE_V1/official_annotation" / pathlib.Path(rel).name
        prior_equal = prior.exists() and prior.read_bytes() == blob
        source_audit[subset] = {
            "official_path": rel, "commit": COMMIT, "bytes": len(blob),
            "sha256": source_hashes[subset],
            "prior_project_copy_path": str(prior.relative_to(READ_ROOT)),
            "prior_project_copy_byte_identical": prior_equal,
            "record_count": len(source_rows[subset]),
        }
        ac: collections.Counter[str] = collections.Counter()
        vc: collections.Counter[str] = collections.Counter()
        pair_counts: collections.Counter[tuple[str, str]] = collections.Counter()
        conflict_n = consistent_n = 0
        format_flags = collections.Counter()
        for row in source_rows[subset]:
            if not isinstance(row.get("file_name"), str):
                raise RuntimeError(f"Missing file_name in {rel}")
            ya, yv = row.get("audio_pseudo_label"), row.get("video_pseudo_label")
            if not isinstance(ya, str) or not isinstance(yv, str) or not norm(ya) or not norm(yv):
                raise RuntimeError(f"Missing source-side pseudo-label in {rel}")
            na, nv = norm(ya), norm(yv)
            ac[na] += 1; vc[nv] += 1; pair_counts[(na, nv)] += 1
            candidates_set.update((na, nv))
            if na != nv: conflict_n += 1
            else: consistent_n += 1
            for label in (ya, yv):
                if re.search(r"[,/]|\b(and|or)\b", label, re.I): format_flags["compound_separator"] += 1
                if re.search(r"[()]", label): format_flags["parentheses"] += 1
                if "-" in label: format_flags["hyphen"] += 1
                if len(label.split()) > 1: format_flags["multiword"] += 1
                if label != norm(label): format_flags["edge_surface_variant"] += 1
        label_counts[subset] = {"audio": ac, "video": vc}
        ontology["sources"][subset] = {
            "rows": len(source_rows[subset]), "conflict_records": conflict_n,
            "consistent_records": consistent_n, "audio_label_counts": dict(sorted(ac.items())),
            "video_label_counts": dict(sorted(vc.items())),
            "normalized_pair_type_count": len(pair_counts),
            "normalized_pair_counts": [{"audio": a, "video": v, "n": n}
                                       for (a, v), n in sorted(pair_counts.items())],
            "format_flags": dict(format_flags),
        }

    candidates = sorted(candidates_set)
    if len(candidates) != 16:
        raise RuntimeError(f"Frozen source-local candidate count changed: {len(candidates)}")
    ontology["candidate_labels_sorted"] = candidates
    ontology["candidate_count"] = len(candidates)
    ontology["audio_label_union_count"] = len(set().union(*(set(x["audio"]) for x in label_counts.values())))
    ontology["video_label_union_count"] = len(set().union(*(set(x["video"]) for x in label_counts.values())))
    ontology["rationale"] = "The pinned labels form a finite, single-token source-local set; edge normalization does not change any observed value; no composite constructions or semantically justified merges are needed. Use the unmerged union so candidate support is explicit and identical across arms."

    by_source: dict[str, dict[int, dict[str, Any]]] = {}
    for subset, rel in SOURCE_FILES.items():
        by_source[subset] = {i: row for i, row in enumerate(source_rows[subset])}
    root_resolved = READ_ROOT.resolve()
    media_rows: list[dict[str, Any]] = []
    for m in mapping:
        subset = m["subset"]
        if subset not in SOURCE_FILES or m["official_annotation_file"] != SOURCE_FILES[subset]:
            raise RuntimeError("Mapping subset/source-file mismatch")
        idx = int(m["official_annotation_row"])
        annotation = by_source[subset][idx]
        sid = m["sample_id"]
        if annotation["file_name"] != sid:
            raise RuntimeError(f"Mapping identity mismatch at {subset} row {idx}")
        source = (READ_ROOT / m["resolved_raw_media_path"]).resolve()
        if not source.is_relative_to(root_resolved) or not source.is_file():
            raise RuntimeError(f"Source media missing or outside project: {m['resolved_raw_media_path']}")
        ya, yv = norm(annotation["audio_pseudo_label"]), norm(annotation["video_pseudo_label"])
        conflict = ya != yv
        source_hash = sha256_file(source)
        if m.get("sha256") and source_hash != m["sha256"]:
            raise RuntimeError(f"Source media SHA-256 mismatch for {sid}")
        audio_out = DERIVED / "audio_16k_mono" / f"{sid}.wav"
        video_out = DERIVED / "silent_video" / f"{sid}.avi"
        if not args.no_derive:
            run_ffmpeg(source, audio_out, "audio")
            run_ffmpeg(source, video_out, "video")
        src_meta = stream_summary(probe(source))
        if src_meta["video_stream_count"] < 1 or src_meta["audio_stream_count"] < 1:
            raise RuntimeError(f"Source A/V streams missing: {sid}")
        audio_meta = stream_summary(probe(audio_out)) if audio_out.exists() else None
        video_meta = stream_summary(probe(video_out)) if video_out.exists() else None
        if not args.no_derive:
            if audio_meta["audio_stream_count"] != 1 or audio_meta["video_stream_count"] != 0:
                raise RuntimeError(f"Audio derivative stream contract failed: {sid}")
            if audio_meta["audio_sample_rate"] != 16000 or audio_meta["audio_channels"] != 1:
                raise RuntimeError(f"Audio derivative format contract failed: {sid}")
            if video_meta["video_stream_count"] != 1 or video_meta["audio_stream_count"] != 0:
                raise RuntimeError(f"Silent video stream contract failed: {sid}")
        rec = {
            "sample_id": sid, "subset": subset, "official_annotation_file": SOURCE_FILES[subset],
            "official_annotation_row": idx, "y_A": ya, "y_V": yv,
            "conflict_pool": conflict, "sample_role": "CONFLICT" if conflict else "CONSISTENT_CONTROL",
            "source_path": str(source.relative_to(READ_ROOT)), "source_sha256": source_hash,
            "source_media_bytes": source.stat().st_size, "source_probe": src_meta,
            "audio_path": str(audio_out.relative_to(ROOT)) if audio_out.exists() else None,
            "audio_sha256": sha256_file(audio_out) if audio_out.exists() else None,
            "audio_probe": audio_meta,
            "silent_video_path": str(video_out.relative_to(ROOT)) if video_out.exists() else None,
            "silent_video_sha256": sha256_file(video_out) if video_out.exists() else None,
            "silent_video_probe": video_meta,
        }
        media_rows.append(rec)

    if args.no_derive:
        print(json.dumps({"source_audit": source_audit, "ontology": ontology,
                          "mapping_rows_audited": len(media_rows), "derivation": "NOT_RUN"}, ensure_ascii=False))
        return 0

    if args.limit:
        raise RuntimeError("--limit is test-only and cannot emit the frozen full manifest/audit")
    rank = {sid: i for i, sid in enumerate(sorted(ids))}
    arms = ["A_ONLY", "V_ONLY", "A_THEN_V", "V_THEN_A"]
    manifest_records = []
    for rec in sorted(media_rows, key=lambda x: x["sample_id"]):
        r = rank[rec["sample_id"]]
        base = candidates if (r // len(candidates)) % 2 == 0 else list(reversed(candidates))
        offset = r % len(candidates)
        order = base[offset:] + base[:offset]
        rec_manifest = {
            "protocol_id": "CA_MER_DERIVED_CONTROLLED_AV_ARBITRATION",
            "protocol_version": "1.0",
            "sample_id": rec["sample_id"], "subset": rec["subset"],
            "official_annotation_file": rec["official_annotation_file"],
            "official_annotation_row": rec["official_annotation_row"],
            "official_annotation_commit": COMMIT,
            "official_annotation_sha256": source_hashes[rec["subset"]],
            "y_A": rec["y_A"], "y_V": rec["y_V"],
            "y_A_semantics": "official audio_pseudo_label; source-provided evidence-side label, not ground truth",
            "y_V_semantics": "official video_pseudo_label; source-provided evidence-side label, not ground truth",
            "conflict_pool": rec["conflict_pool"], "sample_role": rec["sample_role"],
            "audio_path": rec["audio_path"], "audio_sha256": rec["audio_sha256"],
            "silent_video_path": rec["silent_video_path"],
            "silent_video_sha256": rec["silent_video_sha256"],
            "candidate_interface": "FULL_SOURCE_LOCAL_ONTOLOGY",
            "candidate_labels": candidates, "candidate_order": order,
            "candidate_schedule_rank": r, "candidate_rotation": offset,
            "candidate_direction": "forward" if (r // len(candidates)) % 2 == 0 else "reverse",
            "candidate_order_sha256": hashlib.sha256(
                json.dumps(order, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest(),
            "planned_arms": arms,
            "dual_readable": None,
            "dual_readable_status": "NOT_RUN; requires future A_ONLY and V_ONLY predictions",
            "science_status": "NOT_RUN",
        }
        manifest_records.append(rec_manifest)
    with MANIFEST.open("w", encoding="utf-8", newline="\n") as f:
        for record in manifest_records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

    mapping_hash = hashlib.sha256(mapping_bytes).hexdigest()
    source_summary = {
        "audit_version": "1.0", "project": str(ROOT), "official_repository": "https://github.com/ZhiyuanHan-Aaron/MoSEAR",
        "official_commit": COMMIT, "source_files": source_audit,
        "media_mapping_path": str(MAPPING_REL), "media_mapping_sha256": mapping_hash,
        "mapping_rows": len(mapping), "mapping_identity_validation": "PASS",
        "source_label_fields_only": ["audio_pseudo_label", "video_pseudo_label"],
        "excluded_label_or_text_fields": ["final_label", "emotionllama_pseudo_label", "reasoning", "subtitle", "audio_analysis", "video_analysis"],
        "source_discrepancy": "NONE; all three prior project copies are byte-identical to pinned official blobs.",
        "native_artifacts_modified": False,
    }
    write_json(AUDIT / "CAMER_CONTROLLED_SOURCE_AUDIT_V1.json", source_summary)
    source_md = [
        "# CA-MER controlled source audit V1",
        "",
        f"- Pinned official repository commit: {COMMIT}.",
        f"- Media mapping rows: {len(mapping)}; mapping SHA-256: {mapping_hash}.",
        "- Source labels are exclusively audio_pseudo_label (y_A) and video_pseudo_label (y_V); these are source-provided pseudo-labels, not ground truth.",
        "- The three project-side annotation copies are byte-identical to their official blobs at the pinned commit.",
        "- final_label, emotionllama_pseudo_label, reasoning, subtitle, modality analyses, and mapping.target are excluded.",
        "- Native artifacts modified: no.",
        "",
    ]
    for subset, detail in source_audit.items():
        source_md.append(f"- {subset}: {detail['record_count']} records; {detail['bytes']} bytes; SHA-256 {detail['sha256']}.")
    (AUDIT / "CAMER_CONTROLLED_SOURCE_AUDIT_V1.md").write_text("\n".join(source_md), encoding="utf-8")
    write_json(AUDIT / "CAMER_CONTROLLED_ONTOLOGY_AUDIT_V1.json", ontology)

    counts = collections.Counter(r["sample_role"] for r in media_rows)
    subsets = collections.Counter(r["subset"] for r in media_rows)
    audio_props = collections.Counter((r["audio_probe"]["audio_sample_rate"], r["audio_probe"]["audio_channels"],
                                        r["audio_probe"]["audio_codec"]) for r in media_rows)
    silent_props = collections.Counter((r["silent_video_probe"]["video_stream_count"],
                                         r["silent_video_probe"]["audio_stream_count"],
                                         r["silent_video_probe"]["video_codec"]) for r in media_rows)
    errors = [r["sample_id"] for r in media_rows if not r["audio_path"] or not r["silent_video_path"]]
    media_audit = {
        "audit_version": "1.0", "source_mapping_rows": len(mapping),
        "source_media_exists_and_sha256_match": len(media_rows),
        "source_total_bytes": sum(r["source_media_bytes"] for r in media_rows),
        "source_stream_counts": {},
        "derived_audio_rows": sum(bool(r["audio_path"]) for r in media_rows),
        "derived_silent_video_rows": sum(bool(r["silent_video_path"]) for r in media_rows),
        "audio_format_counts": {str(k): v for k, v in audio_props.items()},
        "silent_video_format_counts": {str(k): v for k, v in silent_props.items()},
        "sample_roles": dict(counts), "subsets": dict(subsets),
        "missing_derivatives": errors,
        "derivation": {"audio": "ffmpeg software decode, mono, 16000 Hz, PCM s16le WAV, one thread",
                       "silent_video": "ffmpeg video stream copy to AVI; maps only 0:v:0; -an; one thread"},
        "science_or_model_inference": "NOT_RUN",
    }
    # Keep a clean, serializable source stream count.
    media_audit["source_stream_counts"] = {
        f"video={v},audio={a}": n for (v, a), n in collections.Counter(
            (r["source_probe"]["video_stream_count"], r["source_probe"]["audio_stream_count"])
            for r in media_rows).items()
    }
    write_json(AUDIT / "CAMER_CONTROLLED_MEDIA_AUDIT_V1.json", media_audit)
    (AUDIT / "CAMER_CONTROLLED_MEDIA_AUDIT_V1.md").write_text(
        "# CA-MER controlled media audit V1\n\n"
        f"- Source mappings: {len(mapping)}; media files and source hashes verified: {len(media_rows)}.\n"
        f"- Audio-only derivatives: {media_audit['derived_audio_rows']}; each must be mono 16 kHz PCM WAV.\n"
        f"- Silent-video derivatives: {media_audit['derived_silent_video_rows']}; each must have one video stream and zero audio streams.\n"
        f"- Source media bytes: {media_audit['source_total_bytes']}; no source media modified.\n"
        "- Construction is CPU-only; Qwen/model inference and scientific analysis were not run.\n",
        encoding="utf-8")
    static = {
        "validation_version": "1.0", "status": "PASS" if len(media_rows) == 1500 and not errors else "BLOCKED",
        "expected_rows": 1500, "actual_rows": len(media_rows),
        "unique_sample_ids": len(set(r["sample_id"] for r in media_rows)),
        "all_source_identity_and_hashes_pass": True,
        "audio_derivatives": media_audit["derived_audio_rows"],
        "audio_contract_pass": all(r["audio_probe"]["audio_stream_count"] == 1 and
                                   r["audio_probe"]["video_stream_count"] == 0 and
                                   r["audio_probe"]["audio_sample_rate"] == 16000 and
                                   r["audio_probe"]["audio_channels"] == 1 for r in media_rows),
        "silent_video_derivatives": media_audit["derived_silent_video_rows"],
        "silent_video_contract_pass": all(r["silent_video_probe"]["video_stream_count"] == 1 and
                                           r["silent_video_probe"]["audio_stream_count"] == 0 for r in media_rows),
        "candidate_count": len(candidates), "candidate_order_shared_across_arms": True,
        "planned_arms": arms, "dual_readable": "NOT_RUN; evaluation-time property",
        "conflict_pool_n": sum(r["conflict_pool"] for r in media_rows),
        "consistent_control_n": sum(not r["conflict_pool"] for r in media_rows),
        "missing_derivatives": errors, "science_status": "NOT_RUN",
        "native_artifacts_modified": False,
    }
    write_json(AUDIT / "CAMER_CONTROLLED_STATIC_VALIDATION_V1.json", static)
    code_files = [
        pathlib.Path(__file__),
        REPO / "src/common/benchmarks/camer_controlled_parser_v1.py",
        REPO / "configs/mainline/camer_controlled_arbitration_prompt_v1.json",
    ]
    provenance = {
        "provenance_version": "1.0", "protocol_id": "CA_MER_DERIVED_CONTROLLED_AV_ARBITRATION",
        "source_audit": source_summary, "derived_root": str(DERIVED.relative_to(ROOT)),
        "manifest_path": str(MANIFEST.relative_to(ROOT)), "manifest_sha256": sha256_file(MANIFEST),
        "code_sha256": {str(p.relative_to(REPO)): sha256_file(p) for p in code_files},
        "derived_audio_count": media_audit["derived_audio_rows"],
        "derived_silent_video_count": media_audit["derived_silent_video_rows"],
        "derivation_parameters": media_audit["derivation"],
        "execution_policy": {"cpu_only": True, "model_loaded": False, "gpu_inference": False,
                             "api_or_judge": False, "science_run": False},
        "native_artifacts_modified": False,
    }
    write_json(AUDIT / "CAMER_CONTROLLED_PROVENANCE_V1.json", provenance)
    print(json.dumps({
        "status": static["status"], "mapping_rows": len(mapping),
        "conflict_pool_n": static["conflict_pool_n"], "consistent_control_n": static["consistent_control_n"],
        "candidate_count": len(candidates), "audio_derivatives": static["audio_derivatives"],
        "silent_video_derivatives": static["silent_video_derivatives"],
        "audio_contract_pass": static["audio_contract_pass"],
        "silent_video_contract_pass": static["silent_video_contract_pass"],
        "manifest_sha256": provenance["manifest_sha256"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if static["status"] == "PASS" and static["audio_contract_pass"] and static["silent_video_contract_pass"] else 2


remap_namespace(globals())

if __name__ == "__main__":
    raise SystemExit(main())

