import csv, hashlib, os, sys, subprocess, json
root = sys.argv[1]
os.chdir(root)
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
out = {}
# 1. migration SHA256SUMS
bad=[]; n=0
for line in open('evidence/provenance/recovered_evidence_migration_v1/SHA256SUMS.txt'):
    h,p = line.rstrip('\n').split('  ',1); n+=1
    if not os.path.exists(p) or sha(p)!=h: bad.append(p)
out['migration_sha256sums']={'entries':n,'fail':bad}
for d in ['results/historical_evidence_reconciliation_v2','results/recovered_evidence_scientific_analysis_v1','results/transfer_failure_integration_v1','results/four_regime_structural_synthesis_v1']:
    f=d+'/SHA256SUMS.txt'
    if not os.path.exists(f): continue
    bad=[];miss=[];n=0
    for line in open(f):
        line=line.strip()
        if not line: continue
        h,p=line.split(None,1); p=p.lstrip('*'); n+=1
        q=p if os.path.exists(p) else os.path.join(d,p)
        if not os.path.exists(q): miss.append(p)
        elif sha(q)!=h: bad.append(p)
    out[f]={'entries':n,'missing':miss,'mismatch':bad}
# 2. allowlist
A=list(csv.DictReader(open('evidence/provenance/recovered_evidence_migration_v1/MIGRATION_ALLOWLIST.csv',newline='')))
changed=set(open(sys.argv[2]).read().split())
tb=0; sb=0; mism=[]; bytes_mism=[]; notin=[]; redact=[]
for r in A:
    p=r['target_path']
    if p not in changed: notin.append(p)
    if not os.path.exists(p): mism.append((p,'missing')); continue
    a=sha(p); s=os.path.getsize(p); tb+=s; sb+=int(r['bytes'])
    if a!=r['target_sha256']: mism.append((p,'target_sha'))
    if s!=int(r['bytes']): bytes_mism.append((p,int(r['bytes']),s))
    if (r['byte_identical']=='True') != (r['source_sha256']==r['target_sha256']): mism.append((p,'byte_identical_flag_inconsistent'))
    if r['redacted']=='True': redact.append((p,r['source_sha256'][:12],r['target_sha256'][:12],int(r['bytes']),s,r['transformation_rule'][:160]))
out['allowlist']={'rows':len(A),'unique_targets':len({r['target_path'] for r in A}),'sum_actual_target_bytes':tb,'sum_bytes_column':sb,
  'sha_mismatch':mism,'bytes_column_mismatch':bytes_mism,'not_in_pr_diff':notin,'redacted':redact}
nonpayload=sorted(changed-{r['target_path'] for r in A})
out['non_payload_files']=nonpayload
out['non_payload_bytes']=sum(os.path.getsize(p) for p in nonpayload)
out['total_changed_bytes']=sum(os.path.getsize(p) for p in changed)
print(json.dumps(out,indent=1))
