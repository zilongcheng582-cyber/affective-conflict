"""CURRENT_AUTHORITATIVE_IMPLEMENTATION: corrected B3 measurement contract.

CPU-only identity, assignment, cache and feature schema operations. No target fit
or evaluation; source teacher forcing is supplied by the pinned source module.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from typing import Mapping

DATASET_MODALITIES = {'MCR': ('A', 'T'), 'LISTEN': ('A', 'T'), 'CA-MER': ('A', 'V')}
SEED = 42


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def object_sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def require_sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('A lowercase SHA256 is required')
    return value


def validate_sequences(artifact):
    ontology = artifact['ontology_order']
    seq = artifact['sequences']
    if artifact.get('status') != 'FROZEN' or artifact.get('same_sequence_all_arms_per_utterance') is not True:
        raise ValueError('Source schedule is not frozen across all arms')
    if len(ontology) != 7 or len(set(ontology)) != 7 or len(seq) != 14:
        raise ValueError('Expected authoritative 14 permutations of seven labels')
    if len({r['candidate_sequence_id'] for r in seq}) != 14:
        raise ValueError('Duplicate sequence IDs')
    if len({tuple(r['labels']) for r in seq}) != 14:
        raise ValueError('Duplicate sequences')
    for row in seq:
        if len(row['labels']) != 7 or set(row['labels']) != set(ontology) or row['pipe'] != '|'.join(row['labels']):
            raise ValueError('Sequence is not an ontology permutation')
    return seq


def canonical_sample_id(dataset, stable_dataset_id):
    if dataset not in DATASET_MODALITIES or not isinstance(stable_dataset_id, str) or not stable_dataset_id.strip():
        raise ValueError('Stable dataset identity is required; row indices are not sample identity')
    # Preserve the complete source identity, including condition suffixes.
    # Do not infer equivalence by removing prefixes/suffixes or using row numbers.
    return dataset + ':' + stable_dataset_id


def assign_sequences(populations: Mapping[str, list[str]], source_schedule):
    sequences = validate_sequences(source_schedule)
    result=[]
    for dataset in sorted(populations):
        ids = populations[dataset]
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError('Population identities must be nonempty and unique')
        ordered=sorted(ids)
        q,rem=divmod(len(ordered),14)
        # Source family: sequence-major quota list, extras CS01..CSrem at end,
        # independent Python Random(42), then sorted stable identities.
        schedule=[i for i in range(14) for _ in range(q)] + list(range(rem))
        random.Random(SEED).shuffle(schedule)
        for sid,index in zip(ordered,schedule):
            seq=sequences[index]
            result.append({'dataset':dataset,'sample_id':canonical_sample_id(dataset,sid),
                           'stable_dataset_id':sid,'candidate_sequence_id':seq['candidate_sequence_id'],
                           'candidate_sequence':list(seq['labels'])})
        counts=Counter(schedule)
        if max(counts.get(i,0) for i in range(14))-min(counts.get(i,0) for i in range(14)) > 1:
            raise AssertionError('Assignment balance violation')
    return result


CACHE_FIELDS=('dataset','modality','evidence_hash','candidate_sequence_id',
              'candidate_sequence','prompt_hash','prompt_content_sha256','model_revision','processor_revision',
              'scoring_code_sha256','model_content_sha256','processor_content_sha256')


def cache_identity(task):
    payload={k:task[k] for k in CACHE_FIELDS}
    if payload['dataset'] not in DATASET_MODALITIES or payload['modality'] not in DATASET_MODALITIES[payload['dataset']]:
        raise ValueError('Unexpected dataset/modality')
    for k in ('evidence_hash','prompt_hash','prompt_content_sha256','scoring_code_sha256','model_content_sha256','processor_content_sha256'):
        require_sha(payload[k])
    for k in ('model_revision','processor_revision','candidate_sequence_id'):
        if not isinstance(payload[k],str) or not payload[k].strip():
            raise ValueError('Unresolved runtime/sequence identity: '+k)
    labels=payload['candidate_sequence']
    if not isinstance(labels,list) or len(labels)!=7 or len(set(labels))!=7:
        raise ValueError('Invalid candidate sequence in cache identity')
    return {'cache_key':'b3-corrected-v1:'+object_sha256(payload),'identity':payload}


def build_tasks(evidence_rows, assignments, runtime):
    assignment={(x['dataset'],x['stable_dataset_id']):x for x in assignments}
    measurements=[]
    seen=set()
    for row in sorted(evidence_rows,key=lambda x:(x['dataset'],x['stable_dataset_id'],x['modality'])):
        key=(row['dataset'],row['stable_dataset_id'],row['modality'])
        if key in seen: raise ValueError('Duplicate sample/modality measurement')
        seen.add(key)
        task={**runtime,**row,**assignment[key[:2]]}
        cache=cache_identity(task)
        task.update(inference_cache_key=cache['cache_key'],cache_identity=cache['identity'])
        task['measurement_id']=object_sha256({'dataset':row['dataset'],'sample_id':task['sample_id'],'modality':row['modality']})
        measurements.append(task)
    for (ds,sid),a in assignment.items():
        if {k[2] for k in seen if k[:2]==(ds,sid)} != set(DATASET_MODALITIES[ds]):
            raise ValueError('Both modalities must have locators for each frozen sample')
    forwards={}
    for task in measurements:
        forwards.setdefault(task['inference_cache_key'],task)
    return measurements,list(forwards.values())


def validate_resume_record(record, task, manifest_sha256):
    require_sha(manifest_sha256)
    expected=cache_identity(task)
    if record.get('manifest_sha256')!=manifest_sha256 or record.get('inference_cache_key')!=expected['cache_key'] or record.get('cache_identity')!=expected['identity']:
        raise ValueError('Resume record is stale or unbound')
    if record.get('status') != 'SUCCESS':
        raise ValueError('Explicit technical failure cannot be silently reused')
    if record.get('candidate_sequence')!=task['candidate_sequence'] or record.get('candidate_sequence_id')!=task['candidate_sequence_id']:
        raise ValueError('Resume probability vector belongs to a different candidate order')
    validate_probability_record(record)
    return True


def features(candidate_labels, probabilities, raw_source_label):
    if len(candidate_labels)!=7 or len(set(candidate_labels))!=7 or len(probabilities)!=7:
        raise ValueError('Seven aligned candidate labels/probabilities required')
    if any(not math.isfinite(x) or x<0 or x>1 for x in probabilities) or abs(sum(probabilities)-1)>1e-6:
        raise ValueError('Invalid normalized probability vector')
    h=-sum(p*math.log(p) for p in probabilities if p>0)
    ordered=sorted(probabilities,reverse=True)
    supported=raw_source_label in candidate_labels
    return {'entropy_nats':h,'normalized_entropy':h/math.log(7),
            'top1_top2_margin':ordered[0]-ordered[1],
            'source_label_probability':probabilities[candidate_labels.index(raw_source_label)] if supported else None,
            'source_label_probability_defined':supported}


def measurement_record(task, result, raw_source_label, manifest_sha256):
    labels=result['candidate_labels']
    if labels!=task['candidate_sequence']:
        raise ValueError('Result vector must be aligned to the assigned sequence')
    derived=features(labels,result['candidate_probabilities'],raw_source_label)
    record={k:task[k] for k in ('sample_id','dataset','modality','candidate_sequence_id','candidate_sequence','prompt_hash','evidence_hash','model_revision','processor_revision','scoring_code_sha256')}
    record.update(derived)
    record.update({'candidate_labels':labels,'candidate_probabilities':result['candidate_probabilities'],
                   'manifest_sha256':require_sha(manifest_sha256),'raw_source_label':raw_source_label})
    validate_probability_record(record)
    return record


def validate_probability_record(record):
    if record['candidate_labels']!=record['candidate_sequence']:
        raise ValueError('Candidate output alignment mismatch')
    expected=features(record['candidate_labels'],record['candidate_probabilities'],record.get('raw_source_label'))
    for key in ('normalized_entropy','top1_top2_margin'):
        if not math.isfinite(record[key]) or abs(record[key]-expected[key])>1e-12:
            raise ValueError('Historical feature formula mismatch: '+key)
    for key in ('source_label_probability','source_label_probability_defined'):
        if key in record and record[key]!=expected[key]:
            raise ValueError('Ontology/source probability mismatch')


def robustness_panel(assignments, source_schedule, panel_size=140):
    """Optional identity-only secondary manifest; not invoked by the primary."""
    if not 100<=panel_size<=200: raise ValueError('Preregister 100--200 scientific samples')
    selected=sorted(assignments,key=lambda x:object_sha256({'dataset':x['dataset'],'sample_id':x['sample_id']}))[:panel_size]
    if len(selected)!=panel_size: raise ValueError('Insufficient frozen population')
    return [{**x,'candidate_sequence_id':s['candidate_sequence_id'],'candidate_sequence':list(s['labels']),
             'analysis_role':'SECONDARY_CANDIDATE_ORDER_ROBUSTNESS_ONLY'} for x in selected for s in validate_sequences(source_schedule)]
