"""AutoDL CPU step (before any GPU pilot): bind frozen media and generate intervention audio.

For every eligible item:
  * resolve the frozen source WAV and silent MP4 (AF_DATA_ROOT / AF_PATH_MAPPING, as in the mainline);
  * verify the silent MP4 SHA256 equals EMOTIONTALK_MEDIA_MANIFEST_V1 (fail-closed);
  * record the source WAV SHA256 (no frozen WAV hash exists in the repository; this binding creates it);
  * resolve the official Text JSON (needed only because the frozen pairwise kernel checks it exists);
  * write RECODE / SNR20 / SNR10 / SNR00 files under a NEW media root and record their SHA256 and SNR metadata;
  * if librosa is importable (Qwen env), re-load each written file exactly as qwen-omni-utils does
    (librosa.load(sr=16000)) and record the model-loader SNR against the loaded RECODE file.

  python -m src.emotiontalk.reliability_v1.bind_media --media-root /new/dir --binding-out /new/AUDIO_INTERVENTION_BINDING_V1.csv
  python -m src.emotiontalk.reliability_v1.bind_media --dry-run   # CPU: plan only, no media access
Never overwrites; outputs must not exist.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from src.emotiontalk.reliability_v1 import audio, design


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def plan():
    elig, trials = design.build()
    items = [e for e in elig if e['eligible']]
    files = [(e['utterance_id'], c) for e in items for c in design.CONDITIONS if c != 'CLEAN']
    return items, trials, files


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--media-root', type=Path)
    ap.add_argument('--binding-out', type=Path)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pilot-only', action='store_true', help='bind only the 6 pilot items (separate output)')
    a = ap.parse_args()
    items, trials, files = plan()
    if a.pilot_only:
        items = [e for e in items if e['pilot_selected']]
    if a.dry_run:
        print(json.dumps({'status': 'BIND_PLAN_ONLY', 'items': len(items),
                          'intervention_files': len(items) * (len(design.CONDITIONS) - 1),
                          'media_accessed': False}, indent=1))
        return
    if not a.media_root or not a.binding_out:
        raise SystemExit('--media-root and --binding-out are required')
    if a.media_root.exists() or a.binding_out.exists():
        raise SystemExit('Outputs must be new; refusing to overwrite')
    from src.common.runtime import relocate
    from src.emotiontalk.phase2 import core as p2core
    try:
        import librosa
    except Exception:
        librosa = None
    text_paths = p2core.text_index([e['utterance_id'] for e in items])
    a.media_root.mkdir(parents=True)
    rows = []
    for e in items:
        uid = e['utterance_id']
        src = Path(relocate(e['audio_path_frozen']))
        vid = Path(relocate(e['silent_video_path_frozen']))
        if not src.is_file() or src.stat().st_size == 0:
            raise SystemExit('MISSING_SOURCE_AUDIO ' + uid)
        if not vid.is_file() or sha(vid) != e['silent_video_sha256_frozen']:
            raise SystemExit('SILENT_VIDEO_IDENTITY_FAIL ' + uid)
        src_bytes = src.read_bytes()
        src_sha = hashlib.sha256(src_bytes).hexdigest()
        seed = design.noise_seed(uid)
        loaded = {}
        base = {'utterance_id': uid, 'source_audio_path': str(src), 'source_audio_sha256': src_sha,
                'silent_video_path': str(vid), 'silent_video_sha256': e['silent_video_sha256_frozen'],
                'text_json_path': str(text_paths[uid]), 'text_json_sha256': sha(text_paths[uid]), 'noise_seed': seed}
        rows.append({**base, 'condition': 'CLEAN', 'audio_variant': 'ORIGINAL_FILE', 'intervention_audio_path': str(src),
                     'intervention_audio_sha256': src_sha, 'spec_version': audio.SPEC_VERSION})
        for cond, (variant, snr) in design.CONDITIONS.items():
            if cond == 'CLEAN':
                continue
            out_bytes, meta = audio.make_variant(src_bytes, seed, snr)
            path = a.media_root / 'audio' / cond / f'{uid}.wav'
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'xb') as f:
                f.write(out_bytes)
            if sha(path) != meta['output_sha256']:
                raise SystemExit('WRITE_HASH_MISMATCH ' + str(path))
            row = {**base, 'condition': cond, 'audio_variant': variant, 'intervention_audio_path': str(path),
                   'intervention_audio_sha256': meta['output_sha256'], **{k: v for k, v in meta.items() if k != 'output_sha256'}}
            if librosa is not None:
                y, _ = librosa.load(str(path), sr=audio.TARGET_SR)
                loaded[cond] = y.astype(np.float64)
                row['model_loader_frames'] = len(y)
            rows.append(row)
        if librosa is not None:
            ref = loaded['RECODE']
            for r in rows:
                if r['utterance_id'] == uid and r['condition'].startswith('SNR'):
                    y = loaded[r['condition']]
                    if len(y) == len(ref):
                        r['model_loader_snr_db'] = float(10 * np.log10(np.mean(ref ** 2) / np.mean((y - ref) ** 2)))
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(a.binding_out, 'x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({'status': 'BINDING_WRITTEN', 'items': len(items), 'rows': len(rows),
                      'binding_sha256': sha(a.binding_out), 'librosa_loader_check': librosa is not None}, indent=1))


if __name__ == '__main__':
    main()
