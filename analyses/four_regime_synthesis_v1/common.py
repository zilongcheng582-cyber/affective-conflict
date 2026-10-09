"""FOUR_REGIME_STRUCTURAL_SYNTHESIS_V1: shared CPU helpers.

POST_HOC_EXPLORATORY synthesis. No GPU, no model loading, no refit of any frozen transfer model.
Writes only under results/four_regime_structural_synthesis_v1/.
"""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'results/four_regime_structural_synthesis_v1'
INTER = OUT / 'intermediate'
SEED = 20261009
B = 2000
ORIGIN = 'POST_HOC_EXPLORATORY_FOUR_REGIME_SYNTHESIS_V1'
SCRIPT_VERSION = 'v1.0'
_USED = {}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def used(rel):
    """Register an input file (repo-relative) and return its absolute path."""
    p = REPO / rel
    if rel not in _USED:
        _USED[rel] = sha256(p)
    return p


def used_registry():
    return dict(sorted(_USED.items()))


def save_registry(name):
    INTER.mkdir(parents=True, exist_ok=True)
    (INTER / f'INPUTS_USED_{name}.json').write_text(json.dumps(used_registry(), indent=1))


def git_head():
    return subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()


def read_csv(rel, **kw):
    return pd.read_csv(used(rel), encoding='utf-8-sig', **kw)


def read_jsonl(rel):
    return pd.DataFrame([json.loads(l) for l in open(used(rel), encoding='utf-8') if l.strip()])


def write(df, name, sub=''):
    d = OUT / sub if sub else OUT
    d.mkdir(parents=True, exist_ok=True)
    df.to_csv(d / name, index=False, float_format='%.6g')
    return d / name


# ---------- statistics (numpy/pandas only) ----------
def auroc(y, s):
    y = np.asarray(y, float); s = np.asarray(s, float)
    pos = y == 1; n1 = pos.sum(); n0 = (~pos).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(s).rank().values
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def log_loss(y, p, eps=1e-12):
    y = np.asarray(y, float); p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def wilson(k, n, z=1.959964):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def cluster_boot(clusters, stat, reps=B, seed=SEED):
    """Percentile bootstrap resampling whole clusters. stat(idx_array) -> float. Returns (point, lo, hi, n_defined)."""
    clusters = np.asarray(clusters)
    codes, uniq = pd.factorize(clusters)
    members = [np.where(codes == i)[0] for i in range(len(uniq))]
    rng = np.random.default_rng(seed)
    point = stat(np.arange(len(clusters)))
    vals = []
    for _ in range(reps):
        pick = rng.integers(0, len(members), len(members))
        idx = np.concatenate([members[i] for i in pick])
        v = stat(idx)
        if np.isfinite(v):
            vals.append(v)
    if not vals:
        return (point, np.nan, np.nan, 0)
    return (point, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), len(vals))


def normalized_entropy_from_probs(p):
    p = np.asarray(p, float); p = p[p > 0]
    return float(-(p * np.log(p)).sum() / np.log(7))


def b3_table():
    """Corrected B3 unimodal measurements with top-1 label (7-label EmotionTalk candidate space)."""
    b = read_csv('evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv')
    labs = b.candidate_labels.map(json.loads); probs = b.candidate_probabilities.map(json.loads)
    b['top1_label'] = [l[int(np.argmax(p))] for l, p in zip(labs, probs)]
    b['top1_prob'] = [max(p) for p in probs]
    return b


def logit_fit(X, y, l2=1e-6, iters=60):
    X = np.column_stack([np.ones(len(X)), X]); w = np.zeros(X.shape[1])
    for _ in range(iters):
        z = np.clip(X @ w, -30, 30); p = 1 / (1 + np.exp(-z))
        g = X.T @ (p - y) + l2 * np.r_[0, w[1:]]
        H = (X.T * (p * (1 - p))) @ X + l2 * np.eye(len(w))
        step = np.linalg.solve(H + 1e-9 * np.eye(len(w)), g); w -= step
        if np.abs(step).max() < 1e-9:
            break
    return w


def logit_pred(w, X):
    X = np.column_stack([np.ones(len(X)), X]); return 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
