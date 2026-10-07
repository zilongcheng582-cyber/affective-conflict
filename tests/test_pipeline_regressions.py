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
class CurrentPipelineRegression(unittest.TestCase):

    def test_listen_decodes_only_exact_generated_suffix(self):
        import torch

        class Processor:

            def batch_decode(self, value, **kw):
                return [''.join((chr(x) for x in row.tolist())) for row in value]
        proc = Processor()
        prompt = torch.tensor([[65, 65, 65]])
        generated = torch.tensor([[65, 65, 65, 66]])
        continuation = listen.decode_continuation(generated, {'input_ids': prompt}, proc)
        self.assertEqual(continuation, 'B')
        self.assertEqual(listen.extract_letter(continuation, 2), 'B')
        with self.assertRaises(ValueError):
            listen.decode_continuation(torch.tensor([[66, 65, 65, 66]]), {'input_ids': prompt}, proc)

    def test_publication_cv_same_folds_all_models(self):
        rows = [{'utterance_id': f'g-{i // 2:03d}', 'pair': ('AT', 'AV', 'VT')[i % 3], '_y': i % 2, '_srcz': float(i % 7), '_marz': float(i % 5), '_entz': float(i % 3), '_order': i % 2} for i in range(80)]
        training = []

        def fake_fit(x, y):
            training.append(tuple(y.tolist()))
            return {'ok': True, 'b': __import__('numpy').zeros(x.shape[1])}
        with patch.object(cv, 'fit', side_effect=fake_fit):
            out = cv.compare_models(rows)
        maps = [x['fold_assignment'] for x in out['models'].values()]
        self.assertTrue(all((x == maps[0] for x in maps)))
        self.assertTrue(all((training[i:i + 5] == training[:5] for i in range(0, len(training), 5))))
        for i in range(0, len(rows), 2):
            self.assertEqual(out['folds'][rows[i]['utterance_id']], out['folds'][rows[i + 1]['utterance_id']])
        self.assertFalse(out['historical_full_source_fit_replaced'])

    def test_mcr_resume_all_contract_identities_and_duplicates(self):
        item = {'record_key': 'synthetic:1', 'sample_id': 'synthetic', 'arm': 'A_ONLY', 'candidate_sequence': ['angry'], 'y_audio': 'angry', 'y_text': 'neutral'}
        conf = {'model_revision': 'TEST_ONLY', 'processor_revision': 'TEST_ONLY'}
        contract = mcr.resume_contract([item], {'instruction': 'fixture'}, conf, {'manifest_sha256': 'a' * 64})
        for manifest, prompt, configuration, identity in [([{**item, 'sample_id': 'other'}], {'instruction': 'fixture'}, conf, {'manifest_sha256': 'a' * 64}), ([item], {'instruction': 'different'}, conf, {'manifest_sha256': 'a' * 64}), ([item], {'instruction': 'fixture'}, {**conf, 'model_revision': 'different'}, {'manifest_sha256': 'a' * 64}), ([item], {'instruction': 'fixture'}, conf, {'manifest_sha256': 'b' * 64})]:
            self.assertNotEqual(contract, mcr.resume_contract(manifest, prompt, configuration, identity))
        parsed = mcr.parse_mcr_ser_response('angry')
        record = {**item, **parsed, 'generation_success': True, 'technical_error': None, 'resume_contract_sha256': contract, 'raw_model_output': 'angry'}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'synthetic.jsonl'
            p.write_text(json.dumps(record) + '\n', encoding='utf-8')
            self.assertEqual(mcr.existing_keys(p, {item['record_key']: item}, contract), {item['record_key']})
            with self.assertRaises(ValueError):
                mcr.existing_keys(p, {item['record_key']: item}, 'other')
            p.write_text((json.dumps(record) + '\n') * 2, encoding='utf-8')
            with self.assertRaises(ValueError):
                mcr.existing_keys(p, {item['record_key']: item}, contract)
