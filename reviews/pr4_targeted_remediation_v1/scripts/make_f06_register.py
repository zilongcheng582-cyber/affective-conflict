import json,subprocess,hashlib,os,sys
os.chdir(sys.argv[1])
main=subprocess.check_output(['git','show','544ca0e:manifests/mcr/canonical_arbitration.csv']).decode('utf-8')
targets={
 'results/historical_evidence_reconciliation_v2/MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.public_projection.json':'SANITIZED_DERIVATIVE',
 'results/historical_evidence_reconciliation_v2/MCR_RECONCILIATION_V2.json':'BYTE_IDENTICAL_ORIGINAL',
 'results/historical_evidence_reconciliation_v2/RECONCILIATION_MACHINE_SUMMARY_V2.json':'BYTE_IDENTICAL_ORIGINAL'}
keys={'faithful','adversarial','irrelevant','neutral','native_adversarial_source_text','controlled_text_evidence'}
entries=[]
for f,kind in targets.items():
    def walk(o,p):
        if isinstance(o,dict):
            for k,v in o.items(): yield from walk(v,p+'/'+str(k))
        elif isinstance(o,list):
            for v in o: yield from walk(v,p+'/[]')
        elif isinstance(o,str): yield p,o
    for p,v in walk(json.load(open(f,encoding='utf-8')),''):
        if p.split('/')[-1] in keys and len(v)>=30:
            entries.append({'file':f,'migration_type':kind,'json_path':p,'value_sha256':hashlib.sha256(v.encode()).hexdigest(),'chars':len(v),
                            'verbatim_in_main_canonical_arbitration_csv':v in main})
assert all(e['verbatim_in_main_canonical_arbitration_csv'] for e in entries), [e for e in entries if not e['verbatim_in_main_canonical_arbitration_csv']]
reg={'register':'SANITIZATION_RETAINED_FIELDS_REGISTER_V1','finding':'PR4 review F06','analysis_origin':'MIGRATION_METADATA',
 'rule':'Retained MCR-Bench prompt/assertion strings in public files are allowed only when the exact string is already public in main at 544ca0efae158df369a7b25dd110dc4254f67a7d (manifests/mcr/canonical_arbitration.csv). No new restricted text is introduced; no file content was changed by this register.',
 'main_reference':{'commit':'544ca0efae158df369a7b25dd110dc4254f67a7d','path':'manifests/mcr/canonical_arbitration.csv','sha256':hashlib.sha256(main.encode()).hexdigest()},
 'removed_elsewhere_for_consistency_note':'MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.public_projection.csv dropped native_adversarial_source_text/controlled_text_evidence as unreviewed raw text; the same class of strings is retained here because each retained value is verbatim public in main. LISTEN (MUStARD) and CA-MER raw outputs remain fully removed.',
 'retained_value_count':len(entries),'entries':entries}
out='evidence/provenance/recovered_evidence_migration_v1/SANITIZATION_RETAINED_FIELDS_REGISTER_V1.json'
open(out,'w',encoding='utf-8',newline='\n').write(json.dumps(reg,indent=1,ensure_ascii=False)+'\n')
print(len(entries))
