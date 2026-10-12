"""Targeted regression tests of PR #6 execution/analysis logic on SYNTHETIC fixtures only.

Functions are extracted from the archived source by AST (so the AutoDL-path side effects of
module import never run) and from unchanged main dependencies (frozen commit 34aa1b0, byte-identical
on main). No formal result file is modified. Run:
    PR6=<pr6 checkout> MAIN=<main checkout> python -m unittest -v test_source_logic
and once more under `python -O` to show which gates are assert-only.
"""
import ast, collections, json, os, sys, tempfile, unittest, pathlib, math, hashlib
import numpy as np

PR6 = pathlib.Path(os.environ['PR6']); MAIN = pathlib.Path(os.environ['MAIN'])
E1 = PR6 / 'analyses/emotiontalk_e1_video_v2/source_archive'
E2 = PR6 / 'analyses/emotiontalk_e2_consistent_audio_v1/source_archive'
sys.path.insert(0, str(MAIN))


def extract(path, name, ns):
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), ns)
    return ns[name]


classify_e1 = extract(E1 / 'e1v2_analysis.py', 'classify', {})
stats_e1 = extract(E1 / 'e1v2_analysis.py', 'stats', {'np': np})
holm_e1 = extract(E1 / 'e1v2_analysis.py', 'holm', {})
outcome_e2 = extract(E2 / 'e1e2_analysis.py', 'outcome', {})
estimate_e2 = extract(E2 / 'e1e2_analysis.py', 'estimate', {'np': np, 'BOOT': 10000, 'SIGN': 100000})
load_attempts = extract(E1 / 'e1v2_runner.py', 'load_attempts', {'collections': collections, 'json': json, 'os': os})

from src.common.benchmarks.emotiontalk_controlled_parser_v1 import parse_label  # noqa: E402
CORE_SRC = (MAIN / 'src/emotiontalk/phase2/core.py').read_text()
ORDER = {"A_THEN_V": ("A", "V"), "V_THEN_A": ("V", "A")}
core_build = extract(MAIN / 'src/emotiontalk/phase2/core.py', 'build_messages', {})
core_classify = extract(MAIN / 'src/emotiontalk/phase2/core.py', 'classify', {'ONTOLOGY': ("angry", "disgusted", "fearful", "happy", "neutral", "sad", "surprised")})
uni_build = extract(MAIN / 'src/emotiontalk/phase1/execution.py', 'build_messages', {})


class _Core:  # minimal stand-in exposing only the frozen ORDER table used by inputs()
    pass


_Core.ORDER = ORDER
inputs_ns = {}
inputs = extract(E1 / 'e1e2_common.py', 'inputs', inputs_ns)
# inputs() does `from src.emotiontalk.phase2 import core`; provide a module with the frozen ORDER only
import types  # noqa: E402
_mod = types.ModuleType('src.emotiontalk.phase2.core'); _mod.ORDER = ORDER
sys.modules.setdefault('src.emotiontalk.phase2.core', _mod)
import src.emotiontalk.phase2 as _p2  # noqa: E402
if not hasattr(_p2, 'core'):
    _p2.core = _mod
PROMPT = json.loads((MAIN / 'configs/mainline/emotiontalk_controlled_prompt_v1.json').read_text())

SEQ = 'fearful|happy|neutral|sad|surprised|angry|disgusted'


def trial(arm, yA='angry', yV='neutral', exp='E1'):
    return {'candidate_sequence': SEQ, 'utterance_id': 'U1', 'candidate_sequence_id': 'CS03', 'text_path': '/t.json',
            'audio_path': '/a.wav', 'video_path': '/v.mp4', 'y_A': yA, 'y_V': yV, 'arm': arm, 'experiment': exp}


def gen(label, status='OK', tech=False):
    return {'generation_technical_failure': tech, 'parser_status': status, 'parsed_label': label}


class TestE1Classification(unittest.TestCase):
    def test_side_mapping_uses_frozen_yV_and_yA(self):
        t = trial('A_THEN_V')
        self.assertEqual(classify_e1(t, gen('neutral')), 'SIDE_V')
        self.assertEqual(classify_e1(t, gen('angry')), 'SIDE_A')
        self.assertEqual(classify_e1(t, gen('sad')), 'OTHER')

    def test_yA_yV_swap_swaps_sides(self):
        t = trial('A_THEN_V', yA='neutral', yV='angry')
        self.assertEqual(classify_e1(t, gen('neutral')), 'SIDE_A')
        self.assertEqual(classify_e1(t, gen('angry')), 'SIDE_V')

    def test_parse_fail_not_other(self):
        self.assertEqual(classify_e1(trial('A_THEN_V'), gen(None, 'PARSE_FAIL')), 'PARSE_FAIL')

    def test_parser_exception_status_not_other(self):
        self.assertEqual(classify_e1(trial('A_THEN_V'), gen('sad', 'PARSER_EXCEPTION')), 'PARSE_FAIL')

    def test_generation_failure_is_technical(self):
        self.assertEqual(classify_e1(trial('A_THEN_V'), gen('neutral', tech=True)), 'TECHNICAL_FAILURE')

    def test_scoring_failure_does_not_delete_generation(self):
        r = dict(gen('neutral'), scoring_technical_failure=True)
        self.assertEqual(classify_e1(trial('A_THEN_V'), r), 'SIDE_V')

    def test_core_classify_m1_is_audio_in_AV(self):
        self.assertEqual(core_classify('angry', 'angry', 'neutral'), 'SIDE_M1')
        self.assertEqual(core_classify('Neutral', 'angry', 'neutral'), 'PARSE_FAIL')


class TestE2Classification(unittest.TestCase):
    def test_shared_other_parsefail_tech(self):
        t = trial('A_THEN_V', 'sad', 'sad', 'E2')
        self.assertEqual(outcome_e2(t, {'technical_failure': False, 'parser_status': 'OK', 'parsed_label': 'sad'}), 'SHARED_LABEL')
        self.assertEqual(outcome_e2(t, {'technical_failure': False, 'parser_status': 'OK', 'parsed_label': 'angry'}), 'OTHER')
        self.assertEqual(outcome_e2(t, {'technical_failure': False, 'parser_status': 'PARSE_FAIL', 'parsed_label': None}), 'PARSE_FAIL')
        self.assertEqual(outcome_e2(t, {'technical_failure': True, 'parser_status': 'OK', 'parsed_label': 'sad'}), 'TECH_FAILURE')

    def test_e2_parser_exception_with_label_would_be_counted(self):
        # Documented edge: E2 outcome() only treats PARSE_FAIL/None as parse failure. A PARSER_EXCEPTION record
        # with a stale label would be classified by label. Not reachable in E2 data (0 such rows), recorded as risk.
        t = trial('A_THEN_V', 'sad', 'sad', 'E2')
        self.assertEqual(outcome_e2(t, {'technical_failure': False, 'parser_status': 'PARSER_EXCEPTION', 'parsed_label': 'sad'}), 'SHARED_LABEL')


class TestParser(unittest.TestCase):
    def test_strict(self):
        self.assertEqual(parse_label(' Happy \n')['parsed_label'], 'happy')
        for bad in ['happy.', 'I think happy', 'happy, sad', '', 'joy']:
            self.assertEqual(parse_label(bad)['parser_status'], 'PARSE_FAIL', bad)


class TestInputConstruction(unittest.TestCase):
    def test_orders_place_media_correctly(self):
        a = inputs(trial('A_THEN_V')); b = inputs(trial('V_THEN_A'))
        self.assertEqual((a['evidence_1_modality'], a['evidence_2_modality']), ('A', 'V'))
        self.assertEqual((b['evidence_1_modality'], b['evidence_2_modality']), ('V', 'A'))
        for rec, first in ((a, 'audio'), (b, 'video')):
            msg = core_build(rec, PROMPT)[0]['content']
            self.assertEqual([c['type'] for c in msg], [first, 'video' if first == 'audio' else 'audio', 'text'])
            self.assertEqual(sum(c['type'] == 'audio' for c in msg), 1); self.assertEqual(sum(c['type'] == 'video' for c in msg), 1)
            self.assertIn('/a.wav', [c.get('audio') for c in msg]); self.assertIn('/v.mp4', [c.get('video') for c in msg])

    def test_no_text_evidence_leak(self):
        rec = inputs(trial('A_THEN_V'))
        self.assertIsNone(rec['sample']['text'])
        msg = core_build(rec, PROMPT)[0]['content']
        self.assertFalse(any('Text evidence' in c.get('text', '') for c in msg))

    def test_unimodal_arms_single_modality(self):
        s = inputs(trial('A_ONLY'))
        s['text'] = None
        am = uni_build(s, 'A_ONLY', PROMPT)[0][0]['content']; vm = uni_build(s, 'V_ONLY', PROMPT)[0][0]['content']
        self.assertEqual([c['type'] for c in am], ['audio', 'text']); self.assertEqual([c['type'] for c in vm], ['video', 'text'])

    def test_candidate_order_is_frozen_sequence(self):
        rec = inputs(trial('V_THEN_A'))
        instr = core_build(rec, PROMPT)[0]['content'][-1]['text']
        self.assertIn(', '.join(SEQ.split('|')), instr)


class TestStatistics(unittest.TestCase):
    def test_single_category_zero_vector(self):
        r = stats_e1(np.zeros(20), [f'D{i}' for i in range(20)], 1)
        self.assertEqual(r['p_two_sided'], 1.0); self.assertEqual(r['utterance_ci95'], [0.0, 0.0])

    def test_holm_textbook(self):
        rs = [{'p_two_sided': p} for p in (.01, .04, .03, .2)]
        holm_e1(rs)
        self.assertEqual([round(r['p_holm'], 12) for r in rs], [0.04, 0.09, 0.09, 0.2])

    def test_cluster_ratio_is_item_weighted(self):
        # one big cluster with all effect: ratio bootstrap mean equals item mean, not cluster-mean of means
        d = np.array([1.0] * 10 + [0.0] * 10); cl = ['A'] * 10 + [f'B{i}' for i in range(10)]
        r = stats_e1(d, cl, 3)
        self.assertAlmostEqual(r['effect'], 0.5)
        self.assertTrue(r['dialogue_cluster_ci95'][0] < 0.5 < r['dialogue_cluster_ci95'][1])

    def test_e1_and_e2_estimators_agree(self):
        g = np.random.default_rng(0); d = g.choice([-1, -.5, 0, .5, 1], size=60); cl = [f'D{i // 2}' for i in range(60)]
        a = stats_e1(d, cl, 11); b = estimate_e2(d, cl, 11)
        self.assertEqual(a['p_two_sided'], b['two_sided_signflip_p']); self.assertEqual(a['utterance_ci95'], b['item_ci95'])


class TestAttemptLedger(unittest.TestCase):
    def _write(self, d, recs):
        (d / 'attempts').mkdir()
        for i, r in enumerate(recs):
            (d / 'attempts' / f'{i}.json').write_text(json.dumps(r))

    def test_wrong_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t); self._write(d, [{'trial_id': 'X', 'attempt': 1, 'run_fingerprint': 'BAD'}])
            if sys.flags.optimize:
                by = load_attempts(d, [{'trial_id': 'X'}], 'GOOD')   # assert stripped: gate silently bypassed
                self.assertEqual(by['X'][0]['run_fingerprint'], 'BAD')
            else:
                with self.assertRaises(AssertionError):
                    load_attempts(d, [{'trial_id': 'X'}], 'GOOD')

    def test_duplicate_attempt_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t); r = {'trial_id': 'X', 'attempt': 1, 'run_fingerprint': 'F'}
            self._write(d, [r, r])
            if sys.flags.optimize:
                self.assertEqual(len(load_attempts(d, [{'trial_id': 'X'}], 'F')['X']), 2)
            else:
                with self.assertRaises(AssertionError):
                    load_attempts(d, [{'trial_id': 'X'}], 'F')

    def test_out_of_order_attempt_files_sorted(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            self._write(d, [{'trial_id': 'X', 'attempt': 2, 'run_fingerprint': 'F', 'v': 2}, {'trial_id': 'X', 'attempt': 1, 'run_fingerprint': 'F', 'v': 1}])
            by = load_attempts(d, [{'trial_id': 'X'}], 'F')
            self.assertEqual([r['attempt'] for r in by['X']], [1, 2])
            self.assertEqual(sorted(by['X'], key=lambda r: r['attempt'])[-1]['v'], 2)   # analysis uses last attempt

    def test_journal_repair_appends_missing_only(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t); r = {'trial_id': 'X', 'attempt': 1, 'run_fingerprint': 'F'}
            self._write(d, [r]); load_attempts(d, [{'trial_id': 'X'}], 'F'); load_attempts(d, [{'trial_id': 'X'}], 'F')
            self.assertEqual(len((d / 'trials.jsonl').read_text().splitlines()), 1)

    def test_pending_rule(self):
        # verbatim expression from e1v2_runner.main: retry only after a technical failure, at most 2 attempts
        def pending(by, tid):
            return not by.get(tid) or by[tid][-1]['technical_failure'] and len(by[tid]) < 2
        self.assertTrue(pending({}, 'X'))
        self.assertFalse(pending({'X': [{'technical_failure': False}]}, 'X'))
        self.assertTrue(pending({'X': [{'technical_failure': True}]}, 'X'))
        self.assertFalse(pending({'X': [{'technical_failure': True}, {'technical_failure': True}]}, 'X'))


class TestOrderInteractionSign(unittest.TestCase):
    def test_sign(self):
        # A_THEN_V larger SIDE_V drop than V_THEN_A -> negative interaction for SIDE_V (frozen definition)
        a_rec, a_l3, v_rec, v_l3 = 1, 0, 1, 1
        self.assertEqual((a_l3 - a_rec) - (v_l3 - v_rec), -1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
