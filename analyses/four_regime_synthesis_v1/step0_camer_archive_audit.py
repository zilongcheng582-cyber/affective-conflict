"""READ-ONLY audit of a CA-MER controlled-run archive directory (e.g. audit/QWEN25_CAMER_CONTROLLED_V1).
Usage: python -m analyses.four_regime_synthesis_v1.step0_camer_archive_audit /path/to/audit/QWEN25_CAMER_CONTROLLED_V1 [out.json]
Never writes inside the archive. Answers: which arms/samples exist, whether any score/logit/probability fields exist,
identity agreement with manifests/camer/controlled.jsonl, missing-sample mechanism. Nothing is inferred when a field is absent."""
import collections
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCORE_HINTS = ('logit', 'score', 'logprob', 'log_prob', 'probab', 'entropy')


def main(archive, out=None):
    archive = Path(archive); res = {'archive': str(archive), 'exists': archive.is_dir(), 'files': []}
    if not archive.is_dir():
        res['status'] = 'ARCHIVE_NOT_ACCESSIBLE'; print(json.dumps(res, indent=1)); return res
    meta = {json.loads(l)['sample_id']: json.loads(l) for l in open(REPO / 'manifests/camer/controlled.jsonl') if l.strip()}
    rows = []
    for p in sorted(archive.rglob('*.jsonl')):
        n = 0; keys = collections.Counter(); arms = collections.Counter(); has_arm = False
        for line in open(p, encoding='utf-8', errors='replace'):
            if not line.strip(): continue
            try: r = json.loads(line)
            except Exception: continue
            n += 1; keys.update(r.keys())
            if isinstance(r, dict) and 'arm' in r and 'sample_id' in r:
                has_arm = True; arms[r['arm']] += 1; rows.append((p.name, r))
        res['files'].append(dict(path=str(p.relative_to(archive)), records=n, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), has_arm_and_sample_id=has_arm, arm_counts=dict(arms),
                                 score_like_fields=sorted(k for k in keys if any(h in k.lower() for h in SCORE_HINTS))))
    per = collections.defaultdict(dict)
    for fn, r in rows: per[(r['sample_id'], r['arm'])] = r
    ok = {a: [s for (s, arm) in per if arm == a] for a in ('A_ONLY', 'V_ONLY', 'A_THEN_V', 'V_THEN_A')}
    res['unique_sample_arm_records'] = {a: len(v) for a, v in ok.items()}
    res['samples_not_in_manifest'] = sorted({s for (s, _) in per} - set(meta))[:20]
    res['manifest_samples_missing_per_arm'] = {a: len(set(meta) - set(v)) for a, v in ok.items()}
    stat = collections.Counter((a, r.get('generation_status'), r.get('technical_status'), r.get('error_type')) for (s, a), r in per.items())
    res['status_by_arm'] = {str(k): v for k, v in stat.items()}
    mis = collections.Counter()
    for (s, a), r in per.items():
        m = meta.get(s)
        if not m: continue
        cand = r.get('candidate_order') or r.get('candidate_sequence')
        if cand is not None and cand != m['candidate_order']: mis['candidate_order'] += 1
        for k_arch, k_man in (('audio_sha256', 'audio_sha256'), ('silent_video_sha256', 'silent_video_sha256')):
            if k_arch in r and r[k_arch] != m[k_man]: mis[k_arch] += 1
    res['identity_mismatches'] = dict(mis)
    lab = [(s, r.get('parsed_label')) for (s, a), r in per.items() if a == 'A_ONLY']
    res['A_ONLY_parsed_label_equals_y_A'] = sum(1 for s, l in lab if s in meta and l == meta[s]['y_A'])
    labv = [(s, r.get('parsed_label')) for (s, a), r in per.items() if a == 'V_ONLY']
    res['V_ONLY_parsed_label_equals_y_V'] = sum(1 for s, l in labv if s in meta and l == meta[s]['y_V'])
    res['sixteen_class_scores_recoverable_on_CPU'] = any(f['score_like_fields'] for f in res['files'])
    res['status'] = 'AUDITED'
    print(json.dumps(res, indent=1))
    if out: Path(out).write_text(json.dumps(res, indent=1))
    return res


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
