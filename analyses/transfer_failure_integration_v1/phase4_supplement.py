"""POST_HOC_EXPLORATORY: frozen feature decomposition, protocol chain, native labels."""
import phase4_transfer as a
from pathlib import Path
import json,collections,math
import numpy as np
def main():
 a.verify();binding,baselines,data=a.load();pkg=Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1')
 paths=[pkg/n for n in ['B3_SOURCE_MODEL_BINDING_V1.json','B3_EVALUATION_PLAN_V1.json','B3_CORRECTED_MEASUREMENT_FREEZE_V1.md','B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json','EXECUTION_PACKAGE_MANIFEST.json','b3_protocol.py','run_b3_corrected_measurement.py']]
 amend=Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001')
 paths += [p for p in amend.iterdir() if p.is_file() and p.suffix in ['.md','.json','.py','.txt']]
 lock=[]
 for p in paths:
  if p.is_file():lock.append({'path':str(p),'sha256':a.sha(p),'bytes':p.stat().st_size,'content_read':p.suffix in ['.md','.json','.py']})
 a.save('PHASE4_ADDITIONAL_PROTOCOL_LOCK.json',lock)
 # Exact contract excerpts; no version substitution.
 docs={str(p):p.read_text() for p in paths if p.is_file() and p.suffix=='.md'}
 a.save('PHASE4_PROTOCOL_READBACK.json',docs)
 features=[]
 for role,ds,model,rows,predrole in a.spec(data):
  conf=[r for r in rows if r['source_relation']=='CONFLICT'];parts={'FULL_CONFLICT':conf}
  for order in sorted({r['presentation_order'] for r in conf}):parts['ORDER_'+order]=[r for r in conf if r['presentation_order']==order]
  for label in sorted({r['modality1_source_label'] for r in conf}):parts['SOURCE_A_'+label]=[r for r in conf if r['modality1_source_label']==label]
  for name,part in parts.items():
   valid=[r for r in part if r['outcome'] in ['SIDE_A','SIDE_T','SIDE_V'] and a.predict(r,model,binding) is not None];c=binding['models'][model]['parameter_values'];s=binding['scalers'];strength='source_probability' if model=='M3a' else 'top1_top2_margin';key='delta_source_label_probability_raw' if model=='M3a' else 'delta_top1_top2_margin_raw';coef='delta_source_label_probability_per_SD' if model=='M3a' else 'delta_top1_top2_margin_per_SD'
   terms=[]
   for r in valid:
    terms.append({'intercept':c['intercept_AT']+c.get('pair_'+r['route'],0),'strength':c[coef]*(r[key]-s[strength]['mean'])/s[strength]['sd'],'entropy':c['delta_normalized_entropy_per_SD']*(r['delta_normalized_entropy_raw']-s['normalized_entropy']['mean'])/s['normalized_entropy']['sd'],'order':c['FIRST_IS_MODALITY1']*a.truth(r['FIRST_IS_MODALITY1'])})
   features.append({'route':role,'group':name,'N':len(valid),'logit_component_means':{k:float(np.mean([t[k] for t in terms])) if terms else None for k in ['intercept','strength','entropy','order']},'mean_delta_H7':float(np.mean([r['delta_normalized_entropy_raw'] for r in valid])) if valid else None,'negative_delta_H7_AUROC':a.metric([r['outcome']=='SIDE_A' for r in valid],[-r['delta_normalized_entropy_raw'] for r in valid])['AUROC'] if valid else None,'note':'component decomposition is algebraic; seven-class scores are not full target-task entropy; negative_H rank shown below without probability clipping'})
   # Rank score AUROC must not use probability clipping for signed continuous entropy.
   from scipy.stats import rankdata
   y=np.array([r['outcome']=='SIDE_A' for r in valid]);v=np.array([-r['delta_normalized_entropy_raw'] for r in valid]);n1=int(y.sum());n0=len(y)-n1
   features[-1]['negative_delta_H7_AUROC']=float((rankdata(v)[y].sum()-n1*(n1+1)/2)/(n1*n0)) if n1 and n0 else None
 a.csvsave('phase4_numeric/TRANSFER_FROZEN_LOGIT_DECOMPOSITION.csv',features)
 labels=[];native=a.read(a.O/'03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv');labs={'sad','happy','fearful','angry','surprised','disgusted','neutral'}
 for field in ['y_A','y_T']:
  for label in sorted({r[field] for r in native}):
   rows=[r for r in native if a.truth(r['conflict']) and r[field]==label];ct=collections.Counter(r['joint_outcome'] for r in rows)
   labels.append({'modality':field,'native_label':label,'literal_B3_supported':label in labs,'conceptual_synonym_mapping':'NOT_FROZEN; not introduced','conflict_N':len(rows),'SIDE_A':ct['SIDE_A'],'SIDE_T':ct['SIDE_T'],'OTHER':ct['OTHER'],'OTHER_rate':ct['OTHER']/len(rows) if rows else None,'dual_match_N':sum(r['eligibility_group']=='DUAL_MATCH' for r in rows)})
 a.csvsave('phase4_numeric/LISTEN_NATIVE_LABEL_SUPPORT_AND_OTHER.csv',labels)
 for x in lock:assert a.sha(x['path'])==x['sha256']
 a.verify();print('PHASE4_SUPPLEMENT_COMPLETE',len(lock),len(features),len(labels),flush=True)
if __name__=='__main__':main()
