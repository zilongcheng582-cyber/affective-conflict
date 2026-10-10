import sys,json,hashlib,collections,re
from pathlib import Path
sys.path.insert(0,'/root/autodl-tmp/affective-conflict-recovered-science-v1')
import analysis as a
O=a.O;R=a.R;Q=a.Q
def run():
 ii=a.read(O/'intermediate/MCR_ITEM_IDENTITY_OUTCOMES.csv');m=[]
 for gt in a.LABS:
  rs=[x for x in ii if x['gt']==gt];d=[int(x['irrelevant']==gt)-int(x['neutral']==gt) for x in rs];z=a.cluster_ci(d,[x['audio_sha256'] for x in rs],'MCRlabelcontrast'+gt);m.append({'source_label':gt,'contrast':'irrelevant minus neutral source match',**z,'inference':'predeclared source-label descriptive family; pointwise CI, no confirmatory significance claim'})
 neutral=[]
 for c in a.CONDS:neutral.append({'condition':c,'predicted_label_distribution':dict(collections.Counter(x[c] for x in ii)),'predicted_neutral':a.cluster_ci([int(x[c]=='neutral') for x in ii],[x['audio_sha256'] for x in ii],'MCRpredneutral'+c)})
 allrate={k:a.cluster_ci([int(a.truth(x[k])) for x in ii],[x['audio_sha256'] for x in ii],'MCRinvariance'+k) for k in ['all_four_same_valid','any_change_including_failure']}
 nd=a.cluster_ci([int(x['irrelevant']=='neutral')-int(x['neutral']=='neutral') for x in ii],[x['audio_sha256'] for x in ii],'MCRpredneutralpaired')
 conflict_hash='d6a4044bfffbe760e2f2a0812b8fa45f846fa4f0318b2b8846202de12a1412a7';conflict=[x for x in ii if x['audio_sha256']==conflict_hash]
 extra={'by_source_label_contrast':m,'prediction_distributions':neutral,'predicted_neutral_shift':nd,'invariance_cluster_ci':allrate,'controlled_same_audio_conflicting_GT':conflict}
 a.save('numeric/MCR_SECONDARY_DIAGNOSTICS.json',extra);a.csvsave('intermediate/MCR_LABEL_PAIRED_CONTRASTS.csv',m)
 # Read complete prompt/construct provenance and model metadata, never import historical runners.
 paths=[R/'audit/QWEN25_CAMER_CONTROLLED_V1/CAMER_CONTROLLED_PROTOCOL_V1.json',R/'audit/QWEN25_CAMER_CONTROLLED_V1/CAMER_CONTROLLED_PROTOCOL_V1.md',R/'code/prompts/qwen25_mcr_native_execution_v1.json',R/'code/prompts/qwen25_mcr_controlled_execution_v1.json',R/'code/prompts/mcr_controlled_arbitration_prompt_v2.json',R/'audit/QWEN25_LISTEN_NATIVE_V3/LISTEN_V3_VS_SOURCE_LAUNCH_AUDIT.md',R/'audit/LISTEN_PHASE1_POOL.md']
 inv=a.read(a.E/'FULL_EXPERIMENT_FILE_INVENTORY.json');paths += [Path(x['path']) for x in inv if any(t in x['path'] for t in ['run_listen','LISTEN_NATIVE_PROTOCOL_V1.json','CAMER_SOURCE','CAMER_DATASET']) and Path(x['path']).suffix in ['.py','.json','.md']][:20]
 texts={};locks=[]
 for p in dict.fromkeys(paths):
  if p.is_file():texts[str(p)]=p.read_text();locks.append({'path':str(p),'sha256':a.sha(p),'bytes':p.stat().st_size,'role':'additional read-only contract/identity source; no support-set change'})
 b3=a.read(a.B3);texts['CORRECTED_B3_MODEL_METADATA']={k:sorted({str(x.get(k)) for x in b3}) for k in ['model_revision','model_content_sha256','processor_revision','processor_content_sha256','scoring_code_sha256','status']}
 a.save('ADDITIONAL_SOURCE_CONTRACTS.json',texts);a.save('ADDITIONAL_INPUT_LOCK.json',locks)
 # Primary numeric replay: compare all generated deterministic numerical tables.
 P=O/'replay_same_seed';checks=[]
 names=[str(p.relative_to(O)) for sub in ['numeric','intermediate'] for p in (O/sub).glob('*') if p.is_file() and (P/p.relative_to(O)).exists()]
 names += [n for n in ['01_MCR_PAIRED_TRANSITIONS.csv','01_MCR_LABEL_CONDITION_ASSOCIATIONS.csv','02_CAMER_ELIGIBILITY_AND_COVERAGE.csv','02_CAMER_MATCHED_TRANSITIONS.csv','03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv']]
 for n in names:checks.append({'path':n,'first_sha256':a.sha(O/n),'replay_sha256':a.sha(P/n),'match':a.sha(O/n)==a.sha(P/n)})
 assert all(x['match'] for x in checks);a.save('REPRODUCIBILITY_VERIFICATION.json',{'seed':a.SEED,'primary_numeric_files_compared':len(checks),'all_match':True,'files':checks});print('DIAGNOSTICS_DONE',len(checks),flush=True)
if __name__=='__main__':run()
