"""POST_AUDIT_SCIENTIFIC_ANALYSIS v1: shared CPU helpers (no inference, no frozen-artifact writes)."""
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'results/post_audit/scientific_analysis_v1'
SEED = 20261008
BOOTSTRAPS = 2000
ORIGIN = 'POST_AUDIT_SCIENTIFIC_ANALYSIS_V1'


def csvrows(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def jsonl(path):
    return [json.loads(line) for line in open(path, encoding='utf-8') if line.strip()]


def write_csv(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='raise')
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in fields})


def fmt(v):
    if v is None:
        return ''
    if isinstance(v, (float, np.floating)):
        return '' if not np.isfinite(v) else repr(float(v))
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def auroc(y, p):
    y = np.asarray(y, int)
    pos, neg = (y == 1).sum(), (y == 0).sum()
    if not pos or not neg:
        return np.nan
    rk = rankdata(p)
    return float((rk[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def log_loss(y, p):
    p = np.clip(np.asarray(p, float), 1e-12, 1 - 1e-12)
    y = np.asarray(y, float)
    return float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))))


def brier(y, p):
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def metrics(y, p):
    return {'AUROC': auroc(y, p), 'log_loss': log_loss(y, p), 'Brier': brier(y, p),
            'accuracy_at_0.5': float(np.mean((np.asarray(p) >= .5) == (np.asarray(y) == 1)))}


def grouped_folds(groups, seed, n_splits=5):
    """Same construction as analyses/phase2/publication_cv_math.grouped_fold_map."""
    g = np.asarray(sorted(set(groups)), dtype=object)
    g = g[np.random.default_rng(seed).permutation(len(g))]
    return {x: k for k, part in enumerate(np.array_split(g, n_splits)) for x in part.tolist()}


def cluster_index(cluster_ids):
    uniq, inv = np.unique(np.asarray(cluster_ids, dtype=object).astype(str), return_inverse=True)
    members = [np.flatnonzero(inv == k) for k in range(len(uniq))]
    return uniq, members


def cluster_bootstrap(cluster_ids, stat, B=BOOTSTRAPS, seed=SEED):
    """Percentile cluster bootstrap. stat(idx)->dict of floats. Returns per-key arrays."""
    _, members = cluster_index(cluster_ids)
    rng = np.random.default_rng(seed)
    out = {}
    for _ in range(B):
        pick = rng.integers(0, len(members), len(members))
        idx = np.concatenate([members[k] for k in pick])
        for k, v in stat(idx).items():
            out.setdefault(k, []).append(v)
    return {k: np.asarray(v, float) for k, v in out.items()}


def ci(arr):
    arr = arr[np.isfinite(arr)]
    if not len(arr):
        return (np.nan, np.nan, 0)
    return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)), int(len(arr)))
