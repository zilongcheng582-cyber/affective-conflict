"""CPU tests for EMOTIONTALK_RELIABILITY_INTERVENTION_V1 design assets (no model, no GPU)."""
import csv
import hashlib
import io
import json
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.io import wavfile

from src.emotiontalk.reliability_v1 import audio, design, run


def test_design_regenerates_frozen_assets():
    elig, trials = design.build()
    assert design.ELIGIBILITY_CSV.read_bytes() == design.to_csv_bytes(elig)
    assert design.MANIFEST_CSV.read_bytes() == design.to_csv_bytes(trials)
    rec = json.loads(design.FREEZE_RECORD.read_text(encoding='utf-8'))
    assert rec['files']['experiments/emotiontalk_reliability_v1/FROZEN_TRIAL_MANIFEST_V1.csv'] == design.sha256_bytes(design.to_csv_bytes(trials))
    s = design.summary(elig, trials)
    assert (s['eligible_items'], s['pilot_items'], s['trials_full'], s['trials_pilot']) == (146, 6, 2336, 96)


def test_population_matches_historical_phase2_av_conflict():
    elig, trials = design.build()
    eligible = {e['utterance_id'] for e in elig if e['eligible']}
    hist = {json.loads(l)['utterance_id'] for l in open(design.REPO / design.INPUTS['phase2_responses'])
            if '"pair": "AV"' in l and '"source_relation": "CONFLICT"' in l}
    assert eligible == hist
    ids = {t['trial_id'] for t in trials}
    assert len(ids) == len(trials)
    for u in eligible:  # balanced, fully crossed design per item
        mine = [t for t in trials if t['utterance_id'] == u]
        assert sorted((t['condition'], t['arm']) for t in mine) == sorted(
            [('CLEAN', 'V_ONLY')] + [(c, a) for c in design.CONDITIONS for a in design.ARMS_PER_CONDITION])
        assert len({t['audio_noise_seed'] for t in mine}) == 1


def _stereo_int16(sr=44100, seconds=1.3):
    t = np.arange(int(sr * seconds)) / sr
    left = 0.3 * np.sin(2 * np.pi * 220 * t)
    right = 0.2 * np.sin(2 * np.pi * 330 * t)
    buf = io.BytesIO()
    wavfile.write(buf, sr, (np.column_stack([left, right]) * 32767).astype(np.int16))
    return buf.getvalue()


def test_audio_snr_exact_nested_and_deterministic():
    src = _stereo_int16()
    seed = design.noise_seed('G00001_02_01_024')
    rec, mrec = audio.make_variant(src, seed, None)
    x = wavfile.read(io.BytesIO(rec))[1].astype(np.float64)
    assert mrec['output_sample_rate'] == 16000 and mrec['source_channels'] == 2 and mrec['realized_snr_db'] is None
    noises = {}
    for snr in (20.0, 10.0, 0.0):
        b1, m1 = audio.make_variant(src, seed, snr)
        b2, _ = audio.make_variant(src, seed, snr)
        assert b1 == b2  # reproducible bytes
        assert abs(m1['realized_snr_db'] - snr) < 1e-6
        assert abs(m1['stored_file_snr_db'] - snr) < 0.01
        noises[snr] = wavfile.read(io.BytesIO(b1))[1].astype(np.float64) - x
    r = noises[0.0] / noises[20.0]
    assert np.allclose(r[np.abs(noises[20.0]) > 1e-4], 10.0, rtol=1e-3)  # same base noise, rescaled
    with pytest.raises(ValueError):
        audio.mix(np.zeros(100), np.ones(100), 10.0)


def _fixture_binding(tmp_path, trial):
    wav = tmp_path / 'a.wav'
    wav.write_bytes(_stereo_int16(16000, 0.5))
    vid = tmp_path / 'v.mp4'
    vid.write_bytes(b'not-a-real-video')
    txt = tmp_path / 't.json'
    txt.write_text('{"content": "x"}')
    h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    rows = {}
    for cond in design.CONDITIONS:
        rows[(trial['utterance_id'], cond)] = {
            'utterance_id': trial['utterance_id'], 'condition': cond, 'source_audio_path': str(wav),
            'source_audio_sha256': h(wav), 'intervention_audio_path': str(wav), 'intervention_audio_sha256': h(wav),
            'silent_video_path': str(vid), 'silent_video_sha256': trial['silent_video_sha256_frozen'],
            'text_json_path': str(txt), 'text_json_sha256': h(txt), 'noise_seed': trial['audio_noise_seed']}
    return rows, vid


def test_runner_fail_closed_on_media_identity(tmp_path):
    trials, _ = run.load_manifest('pilot')
    t = next(x for x in trials if x['arm'] == 'A_THEN_V')
    binding, vid = _fixture_binding(tmp_path, t)
    with pytest.raises(SystemExit, match='identity mismatch'):
        run.build_inputs(t, binding, run.HashCache())  # fake video bytes != frozen silent-video hash


class _Inputs(dict):
    def to(self, *_):
        return self

    @property
    def input_ids(self):
        return self['input_ids']


def _kernel_mocks(answer):
    torch = pytest.importorskip('torch')

    class Tok:
        def __call__(self, text, add_special_tokens=False):
            return {'input_ids': [ord(c) % 250 for c in text]}

    class Proc:
        tokenizer = Tok()

        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            parts = [c.get('text', c.get('type')) for c in messages[0]['content']]
            return 'U:' + '|'.join(parts) + '|A:'

        def __call__(self, text, **_):
            ids = torch.tensor([self.tokenizer(text)['input_ids']])
            return _Inputs(input_ids=ids, attention_mask=torch.ones_like(ids))

        def batch_decode(self, *_, **__):
            return [answer]

    class Model:
        device, dtype = 'cpu', torch.float32

        def generate(self, **kw):
            return torch.cat([kw['input_ids'], torch.tensor([[1, 2]])], 1)

        def thinker(self, **kw):
            g = torch.Generator().manual_seed(int(kw['input_ids'].shape[1]))
            return SimpleNamespace(logits=torch.randn(1, kw['input_ids'].shape[1], 256, generator=g))

    class Cuda:
        OutOfMemoryError = RuntimeError
        is_available = staticmethod(lambda: False)
        synchronize = reset_peak_memory_stats = empty_cache = staticmethod(lambda *a, **k: None)

    class TorchShim:
        cuda = Cuda()

        def __getattr__(self, k):
            return getattr(torch, k)

    return TorchShim(), (lambda messages, use_audio_in_video=False: (None, None, None)), Proc(), Model()


def test_frozen_kernels_accept_runner_contracts(tmp_path, monkeypatch):
    from src.emotiontalk.phase1 import execution as e1
    from src.emotiontalk.phase2 import execution as e2, core as p2core
    trials, _ = run.load_manifest('pilot')
    item = trials[0]['utterance_id']
    mine = {(t['condition'], t['arm']): t for t in trials if t['utterance_id'] == item}
    t_joint = mine[('SNR10', 'A_THEN_V')]
    binding, vid = _fixture_binding(tmp_path, t_joint)
    for r in binding.values():
        r['silent_video_sha256'] = hashlib.sha256(vid.read_bytes()).hexdigest()
    patched = {k: dict(v, silent_video_sha256_frozen=binding[(item, 'CLEAN')]['silent_video_sha256']) for k, v in mine.items()}
    monkeypatch.setattr(p2core, 'probe_streams', lambda p: {'video_stream_count': 1, 'audio_stream_count': 0})
    parse = p2core.load_parser()
    prompt = p2core.read_json(p2core.PROMPT_PATH)
    torch, pmi, proc, model = _kernel_mocks(t_joint['y_A'])
    kind, rec = run.build_inputs(patched[('SNR10', 'A_THEN_V')], binding, run.HashCache())
    assert kind == 'JOINT' and rec['evidence_1_modality'] == 'A' and rec['audio_path'].endswith('a.wav')
    out = e2.execute_pairwise_record(rec, 1, proc, model, torch, pmi, parse, prompt)
    assert out['joint_outcome'] == 'SIDE_MODALITY_1' and out['canonical_modality_outcome'] == 'SIDE_A', out.get('failure_message')
    js = run.score_joint(rec, rec['sample'], prompt, proc, model, torch, pmi)
    assert js['joint_scoring_status'] == 'OK' and abs(sum(js['joint_candidate_probabilities_primary'].values()) - 1) < 1e-9
    for arm in ('A_ONLY', 'V_ONLY'):
        cond = 'SNR10' if arm == 'A_ONLY' else 'CLEAN'
        kind, sample = run.build_inputs(patched[(cond, arm)], binding, run.HashCache())
        r = e1.perform_arm(sample, arm, prompt, proc, model, torch, pmi, parse, __import__('collections').Counter())
        assert r['generation_success'] and r['candidate_scoring_status'] == 'OK', r.get('failure_message')
        assert 0 <= r['candidate_entropy_primary']['normalized_by_log7'] <= 1
        r.update(role='UNIMODAL_MEASUREMENT')
        assert run.technical_failure(r) is False


# ---- Pre-execution amendment 001: directional conservative imputation and S7 scope ----

def _records(trials, joint_outcome_by_cond, fail_conds=(), entropy=0.6):
    out = []
    for t in trials:
        r = {'trial_id': t['trial_id'], 'attempt': 1, 'technical_failure': False}
        if t['role'] == 'UNIMODAL_MEASUREMENT':
            r.update({'candidate_entropy_primary': {'normalized_by_log7': entropy}, 'parsed_label': t['y_A']})
        elif t['condition'] in fail_conds:
            r['technical_failure'] = True
        else:
            r.update({'joint_outcome': joint_outcome_by_cond[t['condition']], 'joint_scoring_status': 'NOT_RUN'})
        out.append(r)
    return out


def _run_analysis(records):
    from src.emotiontalk.reliability_v1 import analyze
    _, trials = design.build()
    trials = [{k: str(v) for k, v in t.items()} for t in trials]
    T = analyze.tables(trials, analyze.latest(records))
    return analyze.summarize(T, design.DESIGN_SEED), T


def _small_boot(monkeypatch):
    from src.emotiontalk.reliability_v1 import analyze
    monkeypatch.setattr(analyze, 'N_BOOT', 200)
    monkeypatch.setattr(analyze, 'N_PERM', 2000)
    monkeypatch.setattr(analyze.boot_ci, '__defaults__', (200,))
    monkeypatch.setattr(analyze.signflip_p, '__defaults__', (2000,))


@pytest.mark.parametrize('failing', ['RECODE', 'SNR00'])
def test_reference_or_degraded_failures_cannot_manufacture_h1(monkeypatch, failing):
    """No true effect (always SIDE_V); every joint trial of one contrast condition fails. Old rule (fail -> SIDE_A=1)
    produced D = -1 when RECODE failed; the directional rule must never yield support for H1."""
    _small_boot(monkeypatch)
    _, trials = design.build()
    trials = [{k: str(v) for k, v in t.items()} for t in trials]
    recs = _records(trials, {c: 'SIDE_MODALITY_2' for c in design.CONDITIONS}, fail_conds=(failing,))
    res, _ = _run_analysis(recs)
    p = res['PRIMARY_dSIDE_A_SNR00_minus_RECODE']
    assert p['estimate'] >= 0 and not res['decision']['primary'].startswith('H1_SUPPORTED')
    # failures alone must not produce a contradiction or disconfirmation verdict either (favourable bound used)
    assert res['decision']['primary'] not in ('H1_CONTRADICTED_OPPOSITE_DIRECTION',)
    assert np.isnan(res['SENS_primary_complete_case']['estimate'])  # no complete item survives
    s3 = res['S3_dSIDE_V_SNR00_minus_RECODE']
    assert s3['estimate'] <= 0  # S3 fill is directional against its expected increase


def test_primary_imputation_bounds_and_true_effect(monkeypatch):
    _small_boot(monkeypatch)
    _, trials = design.build()
    trials = [{k: str(v) for k, v in t.items()} for t in trials]
    outs = {c: 'SIDE_MODALITY_1' for c in design.CONDITIONS}
    outs['SNR00'] = 'SIDE_MODALITY_2'
    res, _ = _run_analysis(_records(trials, outs))
    assert res['PRIMARY_dSIDE_A_SNR00_minus_RECODE']['estimate'] == -1.0
    assert res['SENS_primary_complete_case']['estimate'] == -1.0
    cons, fav = res['SENS_primary_missing_data_bounds_point']
    assert cons == fav == -1.0  # no failures -> bounds coincide


def test_s7_is_exploratory_conditional_and_outside_decision(monkeypatch):
    _small_boot(monkeypatch)
    _, trials = design.build()
    trials = [{k: str(v) for k, v in t.items()} for t in trials]
    res, _ = _run_analysis(_records(trials, {c: 'OTHER' for c in design.CONDITIONS}))
    s7 = res['S7_EXPLORATORY_CONDITIONAL_R1_REFERENCE']
    assert s7['status'].startswith('EXPLORATORY') and s7['scale'] == 'CONDITIONAL_BINARY_P(SIDE_A|SIDE)_NOT_ITT'
    assert np.isnan(s7['observed_change_conditional_binary_share_SIDE_A_among_SIDE']['estimate'])  # no SIDE outcomes
    assert 'magnitude_consistent_with_R1' not in res['decision']
    assert res['decision']['S7_role'] == 'EXPLORATORY_CONDITIONAL_REFERENCE_EXCLUDED_FROM_DECISION'
