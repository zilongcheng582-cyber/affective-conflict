import csv,os,sys
os.chdir(sys.argv[1])
src='results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX.csv'
C=list(csv.DictReader(open(src,newline='',encoding='utf-8-sig')))
U={  # upstream_evidence_status, upstream_source (repo path or locked source), interpretation_layer, may_cite_as_confirmatory
 'X2':('PREREGISTERED_CONFIRMATORY_FROZEN','results/eri1_scientific_closure_v1/CLAIM_REGISTER_V1.md (CONFIRMATORY_SUPPORTED: SNR00-RECODE ITT -10.96 pp)','CITATION_ONLY_NO_NEW_TEST','YES_ERI1_PRIMARY_EFFECT_ONLY'),
 'R1_SOURCE':('POST_AUDIT_DIAGNOSTIC_NOT_PREREGISTERED','results/post_audit/scientific_analysis_v1/R1_SOURCE_STRUCTURE_REPORT.md (POST_AUDIT_SCIENTIFIC_ANALYSIS_V1)','CITATION_PLUS_POST_HOC_EXPLANATORY_PROJECTION','NO'),
 'R2_COMP':('POST_AUDIT_DIAGNOSTIC_NOT_PREREGISTERED','results/post_audit/scientific_analysis_v1/R2_COMPOSITIONALITY_REPORT.md (POST_AUDIT_SCIENTIFIC_ANALYSIS_V1)','CITATION_PLUS_POST_HOC_EXPLANATORY_PROJECTION','NO'),
}
for t in ['T_MCR_RANK','T_LISTEN','T_CA_SUPPORT','T_CA_MARGIN']:
    U[t]=('FROZEN_ZERO_REFIT_METRIC_WITH_POST_AUDIT_BASELINE_COMPARISON','results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv; docs/SCIENTIFIC_CLAIM_STATUS_V1.md (frozen role-specific metrics, not a hypothesis acceptance test)','POST_HOC_INTERPRETATION_OF_FROZEN_METRICS','NO')
for t in ['F_MCR_THRESHOLD','F_LISTEN_SELECTION','F_CA_ENTROPY','X1']:
    U[t]=('POST_HOC_EXPLORATORY_OVER_FROZEN_PREDICTIONS','results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv + recovered linkage','POST_HOC_EXPLORATORY_DECOMPOSITION','NO')
for t in ['M5','L4','C5']:
    U[t]=('HISTORICAL_RECORD_OR_PRIOR_AUDIT_FINDING','results/historical_evidence_reconciliation_v2/ (reconciliation) or corrected-B3 audit','CITATION_OF_RECORD','NO')
U['M1']=('HISTORICAL_DESCRIPTIVE_AGGREGATE_PLUS_POST_HOC_PROJECTION','results/historical_evidence_reconciliation_v2/MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.public_projection.csv','POST_HOC_EXPLORATORY_PROJECTION','NO')
for r in C:
    U.setdefault(r['id'],('POST_HOC_EXPLORATORY_ON_RECOVERED_OUTPUTS','recovered historical native outputs (see source_and_code_trace)','POST_HOC_EXPLORATORY_PROJECTION','NO'))
rows=[]
for r in C:
    u=U[r['id']]
    rows.append({'id':r['id'],'category':r['category'],'claim_status_unchanged':r['status'],
      'integration_analysis_origin':r['analysis_origin'],'upstream_evidence_status':u[0],'upstream_source':u[1],
      'interpretation_layer':u[2],'may_be_cited_as_confirmatory':u[3],
      'note':'Companion metadata (PR4 Remediation V1, F10). analysis_origin in CLAIM_EVIDENCE_MATRIX.csv describes how this integration matrix was produced; it does not downgrade or upgrade upstream evidence. No claim status, number or population changed.'})
assert len(rows)==25 and sum(r['may_be_cited_as_confirmatory']!='NO' for r in rows)==1
out='results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX_EVIDENCE_STATUS_V1.csv'
with open(out,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
import collections;print(collections.Counter(r['upstream_evidence_status'] for r in rows))
