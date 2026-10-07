from __future__ import annotations
import csv, datetime as dt, hashlib, json, subprocess
from pathlib import Path
import argparse
def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()
def canon(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
def git(args):
    p = subprocess.run(["git", "-C", str(ROOT/"source/MoSEAR-official"), *args], text=True, capture_output=True)
    return p.stdout.strip()
def probe_media(p):
    try:
        q = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(p)],
            text=True, capture_output=True, timeout=60,
        )
        payload = json.loads(q.stdout) if q.stdout.strip() else {}
        streams = payload.get("streams", [])
        videos = [x for x in streams if x.get("codec_type") == "video"]
        audios = [x for x in streams if x.get("codec_type") == "audio"]
        fmt = payload.get("format", {})
        duration_raw = fmt.get("duration")
        duration = float(duration_raw) if duration_raw is not None else None
        video = videos[0] if videos else {}
        audio = audios[0] if audios else {}
        return {
            "container_readable": q.returncode == 0,
            "duration_seconds": duration,
            "video_stream_count": len(videos),
            "audio_stream_count": len(audios),
            "video_stream_present": bool(videos),
            "audio_stream_present": bool(audios),
            "video_codec": video.get("codec_name", ""),
            "audio_codec": audio.get("codec_name", ""),
            "width": video.get("width"),
            "height": video.get("height"),
            "frame_rate": video.get("avg_frame_rate") or video.get("r_frame_rate", ""),
            "audio_sample_rate": audio.get("sample_rate"),
            "audio_channels": audio.get("channels"),
            "zero_duration": duration is not None and duration <= 0,
            "probe_error": q.stderr.strip()[:500] if q.returncode else "",
        }
    except Exception as e:
        return {
            "container_readable": False,
            "duration_seconds": None,
            "video_stream_count": 0,
            "audio_stream_count": 0,
            "video_stream_present": False,
            "audio_stream_present": False,
            "video_codec": "",
            "audio_codec": "",
            "width": None,
            "height": None,
            "frame_rate": "",
            "audio_sample_rate": None,
            "audio_channels": None,
            "zero_duration": False,
            "probe_error": repr(e)[:500],
        }
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);ap.add_argument("--hf-ref",type=Path,required=True);a=ap.parse_args()
    global ROOT,OUT
    ROOT = a.root.resolve()
    INPUT = ROOT / "audit" / "QWEN25_CAMER_NATIVE_V1"
    OUT = a.output.resolve()
    if OUT.exists():raise ValueError("Output must be a new directory")
    if OUT.is_relative_to(ROOT):raise ValueError("Output must be outside the acquired input root")
    ANN = INPUT / "official_annotation"
    CODE = INPUT / "official_code"
    MAP = ROOT / "audit" / "CA_MER" / "camer_mer2023_mapping.csv"
    AUTH_MEDIA_ROOT = ROOT / "data/MER2023/full_extract_auth"
    MEDIA_ROOTS = ([AUTH_MEDIA_ROOT] if AUTH_MEDIA_ROOT.exists() else [ROOT/"data/MER2023/extracted", ROOT/"data/MER2023/full_extract"])
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {
        "video-aligned": ANN/"video-aligned.json",
        "audio-aligned": ANN/"audio-aligned.json",
        "consistent": ANN/"consistent.json",
    }
    data = {k: json.loads(p.read_text(encoding="utf-8")) for k,p in paths.items()}
    commit = git(["rev-parse", "HEAD"])
    remote = git(["remote", "get-url", "origin"])
    tree = git(["ls-tree", "-r", "--name-only", "HEAD"]).splitlines()
    inventory = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "official_commit": commit, "files": [], "subsets": {}}
    semantics = {}
    for subset, rows in data.items():
        p = paths[subset]
        fields = sorted(rows[0]) if rows else []
        if subset == "video-aligned":
            bad = [r["file_name"] for r in rows if not (r["video_pseudo_label"] == r["final_label"] and r["audio_pseudo_label"] != r["final_label"])]
        elif subset == "audio-aligned":
            bad = [r["file_name"] for r in rows if not (r["audio_pseudo_label"] == r["final_label"] and r["video_pseudo_label"] != r["final_label"])]
        else:
            bad = [r["file_name"] for r in rows if not (r["audio_pseudo_label"] == r["video_pseudo_label"] == r["final_label"])]
        semantics[subset] = {"records": len(rows), "violations": bad, "verified": not bad}
        inventory["subsets"][subset] = {
            "record_count": len(rows), "schema": fields,
            "file_name_first": rows[0]["file_name"] if rows else None,
            "file_name_last": rows[-1]["file_name"] if rows else None,
            "file_name_unique": len({r["file_name"] for r in rows}) == len(rows),
            "sha256": sha256(p), "canonical_json_sha256": canon(rows),
        }
        inventory["files"].append({"path": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size, "sha256": sha256(p)})
    if any(len(rows)!=500 for rows in data.values()) or not all(x['verified'] for x in semantics.values()):
        raise ValueError("CA-MER official population/subset semantics mismatch")
    all_ids=[r['file_name'] for rows in data.values() for r in rows]
    if len(set(all_ids))!=1500:raise ValueError("Duplicate CA-MER identities")
    final_labels = sorted({r["final_label"] for rows in data.values() for r in rows})
    pseudo_labels = sorted({r[f] for f in ("audio_pseudo_label","video_pseudo_label") for rows in data.values() for r in rows})
    inventory["ontology"] = {
        "final_label_count": len(final_labels), "canonical_final_labels": final_labels,
        "audio_video_pseudo_surface_form_count": len(pseudo_labels), "audio_video_pseudo_surface_forms": pseudo_labels,
        "multi_label_annotation": False, "open_vocabulary_annotation": False, "target_field": "final_label",
    }
    (OUT/"CAMER_ANNOTATION_INVENTORY_V1.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    eval_info = {}
    for fn in ("audio_aligned.txt","video-aligned.txt","consistent.txt"):
        p = CODE/fn
        rows = [x.split() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        subset = fn.replace(".txt","").replace("_","-")
        if subset not in data: subset = "consistent"
        amap = {r["file_name"]: r["final_label"] for r in data[subset]}
        eval_info[fn] = {
            "records": len(rows), "field_count_distribution": sorted({len(x) for x in rows}),
            "sha256": sha256(p), "ids_match_annotation": {x[0] for x in rows} == set(amap),
            "targets_match_annotation": all(len(x)>=3 and x[0] in amap and x[2] == amap[x[0]] for x in rows),
            "first_rows": rows[:3],
        }
    required = ["CA-MER/audio-aligned.json","CA-MER/consistent.json","CA-MER/video-aligned.json","README.md","eval_emotion.py","eval_emotion_EMER.py","emer_evaluation/","eval_configs/","eval_file/","minigpt4/","scripts/","train_configs/"]
    tree_presence = {x: any(y == x or y.startswith(x) for y in tree) for x in required}
    code_hashes = [{"path": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(CODE.glob("*")) if p.is_file()]
    hf_ref_p = a.hf_ref
    hf_ref = hf_ref_p.read_text().strip() if hf_ref_p.exists() else None
    hf_readme = ROOT/"data/MER2023/hf_release/README.md"
    archives = [{"path": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size} for p in sorted((ROOT/"data/MER2023/hf_release").glob("mer2023train.*"))]
    archives += [{"path": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size} for p in sorted((ROOT/"data/MER2023/hf_release").glob("mer2023test1&2.zip"))]
    index = {}
    for mr in MEDIA_ROOTS:
        if mr.exists():
            for p in mr.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".avi",".mp4",".mov",".mkv"}:
                    index.setdefault(p.stem, []).append(p)
    map_rows = list(csv.DictReader(MAP.open(newline="", encoding="utf-8")))
    probe_cache = {}
    required_ids = {r["id"] for r in map_rows}
    for sid in required_ids:
        for p in set(index.get(sid, [])):
            probe_cache[str(p)] = probe_media(p)
    row_lookup = {}
    for subset, rows in data.items():
        for i, r in enumerate(rows):
            row_lookup[r["file_name"]] = (subset, i, r["final_label"])
    mapping_path = OUT/"CAMER_MEDIA_MAPPING_V1.csv"
    fields = ["sample_id","official_annotation_file","official_annotation_row","subset","target","raw_mer2023_archive","raw_mer2023_member","resolved_raw_media_path","resolution_method","file_exists","unique_mapping","media_size_bytes","sha256","container_readable","duration_seconds","video_stream_count","audio_stream_count","video_stream_present","audio_stream_present","video_codec","audio_codec","width","height","frame_rate","audio_sample_rate","audio_channels","zero_duration","probe_error"]
    with mapping_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in map_rows:
            sid = r["id"]; subset, ai, target = row_lookup.get(sid, ("unknown",-1,""))
            archive = r.get("archive_members","")
            ap, member = archive.split("::",1) if "::" in archive else (archive,"")
            cand = sorted(set(index.get(sid, [])))
            exists = len(cand) == 1
            probe = probe_cache.get(str(cand[0]), {}) if exists else {}
            w.writerow({"sample_id":sid,"official_annotation_file":f"CA-MER/{subset}.json","official_annotation_row":ai,"subset":subset,"target":target,"raw_mer2023_archive":ap,"raw_mer2023_member":member,"resolved_raw_media_path":str(cand[0].relative_to(ROOT)) if exists else "","resolution_method":"exact basename over extracted official-media roots" if cand else "exact official archive member; not materialized as decodable raw file","file_exists":exists,"unique_mapping":len(cand)==1,"media_size_bytes":cand[0].stat().st_size if exists else "","sha256":sha256(cand[0]) if exists else "","container_readable":probe.get("container_readable",False),"duration_seconds":probe.get("duration_seconds",""),"video_stream_count":probe.get("video_stream_count",0),"audio_stream_count":probe.get("audio_stream_count",0),"video_stream_present":probe.get("video_stream_present",False),"audio_stream_present":probe.get("audio_stream_present",False),"video_codec":probe.get("video_codec",""),"audio_codec":probe.get("audio_codec",""),"width":probe.get("width",""),"height":probe.get("height",""),"frame_rate":probe.get("frame_rate",""),"audio_sample_rate":probe.get("audio_sample_rate",""),"audio_channels":probe.get("audio_channels",""),"zero_duration":probe.get("zero_duration",False),"probe_error":probe.get("probe_error","")})
    total = len(map_rows)
    physical_unique = sum(len(set(index.get(r["id"],[]))) == 1 for r in map_rows)
    physical_missing = sum(len(index.get(r["id"],[])) == 0 for r in map_rows)
    physical_ambiguous = sum(len(set(index.get(r["id"],[]))) > 1 for r in map_rows)
    archive_mapped = sum(bool(r.get("archive_members")) for r in map_rows)
    probe_rows = [probe_cache[str(sorted(set(index[r["id"]]))[0])] for r in map_rows if len(set(index.get(r["id"], []))) == 1]
    container_readable = sum(x["container_readable"] for x in probe_rows)
    video_stream_present = sum(x["video_stream_present"] for x in probe_rows)
    audio_stream_present = sum(x["audio_stream_present"] for x in probe_rows)
    missing_video_stream = sum(not x["video_stream_present"] for x in probe_rows)
    missing_audio_stream = sum(not x["audio_stream_present"] for x in probe_rows)
    zero_duration = sum(x["zero_duration"] for x in probe_rows)
    dataset_complete = (physical_missing == 0 and physical_ambiguous == 0 and container_readable == total and video_stream_present == total and audio_stream_present == total)
    integrity = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "official_mer2023_source": {"dataset_id":"MERChallenge/MER2023","huggingface_ref":hf_ref,"local_root":str((ROOT/"data/MER2023").relative_to(ROOT)),"readme_sha256":sha256(hf_readme) if hf_readme.exists() else None,"license_seen":"cc-by-nc-4.0","gated_noncommercial_notice_seen":True},
        "archive_files": archives, "required_media_total":total, "archive_member_mapped":archive_mapped,
        "raw_media_materialized_unique":physical_unique, "raw_media_missing":physical_missing, "raw_media_ambiguous":physical_ambiguous,
        "container_readable":container_readable, "container_unreadable":physical_unique - container_readable, "video_stream_present":video_stream_present, "audio_stream_present":audio_stream_present,
        "probe_status":"COMPLETED_WITH_FFPROBE" if physical_unique else "NO_MATERIALIZED_MEDIA_TO_PROBE",
        "full_file_sha256_status":"ALL_UNIQUE_MATERIALIZED_FILES_HASHED" if physical_missing == 0 else "AVAILABLE_FILES_HASHED_IN_MAPPING; MISSING_ARCHIVE-ONLY_FILES_HAVE_NO_HASH",
        "official_media_checksum":"OFFICIAL_MEDIA_CHECKSUM_NOT_AVAILABLE",
        "missing_video_stream":missing_video_stream, "missing_audio_stream":missing_audio_stream,
        "zero_duration":zero_duration, "duplicate_resolved_files":physical_ambiguous,
        "blocking_reason":"" if dataset_complete else "Required raw media are not all uniquely materialized with readable video and audio streams.",
    }
    (OUT/"CAMER_MEDIA_INTEGRITY_V1.json").write_text(json.dumps(integrity, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    prov = {"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"official_repository":"https://github.com/ZhiyuanHan-Aaron/MoSEAR.git","git_remote_origin":remote,"official_commit":commit,"git_history_available":True,"git_tree_entry_count":len(tree),"required_tree_presence":tree_presence,"worktree_clean":not bool(git(["status","--porcelain"])),"worktree_note":"Required files are read from the user-acquired official source checkout; no source files are written.","annotation_files":inventory["files"],"evaluation_lists":eval_info,"official_code_files":code_hashes,"dataset_provenance":integrity["official_mer2023_source"],"no_model_loaded":True,"science_status":"NOT_RUN"}
    (OUT/"CAMER_OFFICIAL_SOURCE_PROVENANCE_V1.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({'output':str(OUT),'canonical_records':len(all_ids),
                      'raw_media_unique':physical_unique,'raw_media_missing':physical_missing,
                      'RAW_TO_CANONICAL_DATA':'PASS' if dataset_complete else 'BLOCKED'},sort_keys=True))
    if not dataset_complete:raise RuntimeError("Required official raw media are incomplete or undecodable")
if __name__=="__main__":main()
