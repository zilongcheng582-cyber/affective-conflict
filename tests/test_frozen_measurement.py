"""Retained current CPU regressions; synthetic model fixture only."""
import ast,copy,hashlib,importlib.util,json,math,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from src.common.runtime import REPO
from src.cross_regime.target_scoring import b3_protocol as b3,b3_scorer as scorer,source_teacher_forcing as teacher
from analyses.phase2 import publication_cv as cv
from src.cross_regime import run_mcr_joint as mcr,run_listen_joint as listen
TREE=REPO
def read_json(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def schedule():return read_json(REPO/'frozen/candidate_sequences/definition.json')

def runtime():
    return {'prompt_hash':'a'*64,'prompt_content_sha256':'a'*64,
            'model_revision':'SYNTHETIC_MODEL_REVISION_FOR_TESTS_ONLY','processor_revision':'SYNTHETIC_PROCESSOR_REVISION_FOR_TESTS_ONLY',
            'model_content_sha256':'b'*64,'processor_content_sha256':'c'*64,
            'scoring_code_sha256':scorer.implementation_sha256(),'manifest_sha256':'d'*64}

def task(sequence_index=0):
    seq=schedule()['sequences'][sequence_index]
    return {**runtime(),'dataset':'LISTEN','modality':'T','evidence_hash':hashlib.sha256(b'fixture').hexdigest(),
            'candidate_sequence_id':seq['candidate_sequence_id'],'candidate_sequence':list(seq['labels']),
            'sample_id':'LISTEN:synthetic-stable-id','stable_dataset_id':'synthetic-stable-id'}

class ProtocolRegression(unittest.TestCase):

    def test_authoritative_sequences(self):
        self.assertEqual(len(b3.validate_sequences(schedule())), 14)
        broken = copy.deepcopy(schedule())
        broken['sequences'][0]['labels'][1] = broken['sequences'][0]['labels'][0]
        with self.assertRaises(ValueError):
            b3.validate_sequences(broken)

    def test_exact_source_assignment_family(self):
        import csv
        path = REPO / 'manifests/emotiontalk/source_measurements.csv'
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1500)
        regenerated = b3.assign_sequences({'MCR': [x['utterance_id'] for x in rows]}, schedule())
        expected = {r['utterance_id']: r['candidate_sequence_id'] for r in rows}
        self.assertEqual({r['stable_dataset_id']: r['candidate_sequence_id'] for r in regenerated}, expected)

    def test_assignment_order_independence_and_balance(self):
        from collections import Counter
        population = {'MCR': [f'stable-{i:04d}' for i in range(909)], 'LISTEN': [f'item-{i:04d}' for i in range(768)], 'CA-MER': [f'clip-{i:04d}' for i in range(1500)]}
        first = b3.assign_sequences(population, schedule())
        second = b3.assign_sequences({k: list(reversed(v)) for k, v in reversed(list(population.items()))}, schedule())
        self.assertEqual(b3.canonical_bytes(first), b3.canonical_bytes(second))
        for ds in population:
            counts = Counter((x['candidate_sequence_id'] for x in first if x['dataset'] == ds))
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_same_sample_same_sequence_all_modalities(self):
        populations = {'MCR': ['stable-a'], 'CA-MER': ['stable-v'], 'LISTEN': ['stable-t']}
        assignments = b3.assign_sequences(populations, schedule())
        evidence = [{'dataset': ds, 'stable_dataset_id': sid, 'modality': mo, 'evidence_hash': 'e' * 64, 'raw_source_label': 'neutral'} for ds, ids in populations.items() for sid in ids for mo in b3.DATASET_MODALITIES[ds]]
        rows, _ = b3.build_tasks(evidence, assignments, runtime())
        for ds in populations:
            group = [x for x in rows if x['dataset'] == ds]
            self.assertEqual(len(group), 2)
            self.assertEqual(group[0]['candidate_sequence'], group[1]['candidate_sequence'])
            self.assertEqual(group[0]['candidate_sequence_id'], group[1]['candidate_sequence_id'])

    def test_cache_reuse_same_evidence_same_sequence(self):
        a = task()
        b = {**a, 'sample_id': 'LISTEN:another-stable-id', 'raw_source_label': 'unsupported'}
        self.assertEqual(b3.cache_identity(a), b3.cache_identity(b))

    def test_cache_never_reuses_different_sequence(self):
        a = task(0)
        b = task(1)
        self.assertNotEqual(b3.cache_identity(a)['cache_key'], b3.cache_identity(b)['cache_key'])

    def test_every_cache_contract_component_changes_identity(self):
        a = task()
        base = b3.cache_identity(a)['cache_key']
        for key, value in [('dataset', 'MCR'), ('modality', 'A'), ('evidence_hash', '0' * 64), ('candidate_sequence_id', 'CS99'), ('prompt_hash', '1' * 64), ('prompt_content_sha256', '0' * 64), ('model_revision', 'OTHER'), ('processor_revision', 'OTHER'), ('scoring_code_sha256', '2' * 64), ('model_content_sha256', '3' * 64), ('processor_content_sha256', '4' * 64)]:
            with self.subTest(field=key):
                self.assertNotEqual(base, b3.cache_identity({**a, key: value})['cache_key'])
        self.assertNotEqual(base, b3.cache_identity({**a, 'candidate_sequence': list(reversed(a['candidate_sequence']))})['cache_key'])

    def test_unresolved_runtime_identity_fails_closed(self):
        for field in ('model_revision', 'processor_revision', 'model_content_sha256', 'processor_content_sha256'):
            with self.subTest(field=field), self.assertRaises((ValueError, KeyError)):
                b3.cache_identity({**task(), field: None})

    def test_feature_alignment_and_structural_unsupported(self):
        a = task(3)
        p = [0.1, 0.2, 0.3, 0.1, 0.1, 0.1, 0.1]
        values = b3.features(a['candidate_sequence'], p, 'anger')
        self.assertIsNone(values['source_label_probability'])
        self.assertFalse(values['source_label_probability_defined'])
        self.assertAlmostEqual(values['top1_top2_margin'], 0.1)
        self.assertAlmostEqual(values['normalized_entropy'], -sum((x * math.log(x) for x in p)) / math.log(7))
        label = a['candidate_sequence'][2]
        self.assertEqual(b3.features(a['candidate_sequence'], p, label)['source_label_probability'], 0.3)

    def test_schema_and_resume_manifest_binding(self):
        a = task(1)
        p = [1 / 7] * 7
        rec = b3.measurement_record(a, {'candidate_labels': a['candidate_sequence'], 'candidate_probabilities': p}, 'unsupported', 'd' * 64)
        required = read_json(REPO / 'protocols/b3/output_schema.json')['required_fields']
        self.assertTrue(set(required) <= set(rec))
        result = {**rec, **b3.cache_identity(a), 'status': 'SUCCESS', 'inference_cache_key': b3.cache_identity(a)['cache_key'], 'cache_identity': b3.cache_identity(a)['identity']}
        self.assertTrue(b3.validate_resume_record(result, a, 'd' * 64))
        with self.assertRaises(ValueError):
            b3.validate_resume_record(result, a, 'f' * 64)
        with self.assertRaises(ValueError):
            b3.validate_resume_record({**result, 'candidate_sequence': list(reversed(a['candidate_sequence']))}, a, 'd' * 64)

class TeacherForcingCPUFixture(unittest.TestCase):

    def test_historical_token_mean_softmax_with_multitoken_candidates(self):
        import torch
        from types import SimpleNamespace
        labels = task()['candidate_sequence']
        tokens = {label: [i + 1] for i, label in enumerate(labels)}
        tokens[labels[0]] = [1, 8]

        class Tokenizer:

            def __call__(self, text, **kwargs):
                ids = [100]
                for label in labels:
                    if text.endswith('CONT:' + label):
                        ids += tokens[label]
                        break
                return {'input_ids': ids}

        class Inputs(dict):

            def to(self, *args):
                return self

        class Processor:
            tokenizer = Tokenizer()

            def apply_chat_template(self, messages, **kwargs):
                self.messages = messages
                return 'CONT:'

            def __call__(self, **kwargs):
                return Inputs(input_ids=torch.tensor([[100]]), attention_mask=torch.tensor([[1]]))

        class Model:
            device = 'cpu'
            dtype = torch.float32
            calls = 0

            def thinker(self, **kw):
                self.calls += 1
                logits = torch.arange(128, dtype=torch.float32).reshape(1, 1, 128).repeat(1, kw['input_ids'].shape[1], 1) / 100
                return SimpleNamespace(logits=logits)

            def generate(self, *args, **kwargs):
                raise AssertionError('Generation forbidden')
        prompt = read_json(REPO / 'configs/mainline/emotiontalk_controlled_prompt_v1.json')
        a = {**task(), 'prompt_content_sha256': b3.object_sha256(prompt)}
        proc = Processor()
        model = Model()
        result = scorer.score_evidence(a, {'text': 'fixture', 'locator': 'synthetic'}, prompt, proc, model, torch, lambda *args, **kwargs: (None, None, None))
        logp = torch.log_softmax(torch.arange(128, dtype=torch.float32) / 100, dim=-1)
        means = [sum((float(logp[i]) for i in tokens[label])) / len(tokens[label]) for label in labels]
        expected = teacher.stable_softmax(means)
        for x, y in zip(result['candidate_probabilities'], expected):
            self.assertAlmostEqual(x, y, places=7)
        self.assertEqual(result['candidate_labels'], a['candidate_sequence'])
        self.assertEqual(model.calls, 2)
        self.assertFalse(result['model_generate_called'])
        self.assertIn(', '.join(labels), str(proc.messages))
        with self.assertRaises(ValueError):
            scorer.score_evidence({**a, 'evidence_hash': '0' * 64}, {'text': 'fixture'}, prompt, proc, model, torch, lambda *a, **k: (None, None, None))
