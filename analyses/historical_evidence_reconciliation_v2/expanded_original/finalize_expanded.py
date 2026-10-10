import json,csv,hashlib,re,shutil,time,zipfile
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');O=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1')
load=lambda n:json.loads((O/n).read_text())
S=load('FULL_EXPERIMENT_SCAN_SUMMARY.json');E=load('EXPERIMENT_EXECUTION_INDEX.json');C=load('DOC_PATH_CLAIMS.json');M=load('MCR_NATIVE_FOUR_CONDITION_RECOVERY.json');raw=load('FULL_EXPERIMENT_EXECUTION_CANDIDATES.json')
SUP=load('OWN_CODE_AND_CHECKPOINT_SUPPLEMENT.json')
groups={}
for r in raw:groups.setdefault(r['sha256'],[]).append(r)
reverse=[r for r in raw if r.get('conditions',{}).get('T_THEN_A') and (r.get('datasets',{}).get('LISTEN') or 'LISTEN_NATIVE' in r['path'])]
fields=['path','sha256','rows','raw_output_present','generation_success_explicit','generation_failure_explicit','conditions','statuses','filename_explicit_in_core_docs','directory_explicit_in_core_docs','evidence_kind','identical_byte_paths']
with open(O/'RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv','x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in E:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],(dict,list)) else r[k] for k in fields})
with open(O/'DOC_REFERENCE_RECONCILIATION.csv','x',newline='') as f:
 fields2=['doc','line','reference','resolved','exists','interpretation','alternatives'];w=csv.DictWriter(f,fieldnames=fields2);w.writeheader()
 for c in C:
  w.writerow({k:c[k] for k in ['doc','line','reference','resolved','exists']}|{'interpretation':'LOCATED_REFERENCE_NOT_PROOF_OF_EXECUTION' if c['exists'] else 'CONCEPTUAL_PHRASE_FALSE_PATH_MATCH','alternatives':json.dumps(c['alternatives'])})
report=f'''# Full project-local experiment evidence recovery

RETROSPECTIVE_EVIDENCE_RECOVERY

## Scope and method
Only /root/autodl-tmp/affective-conflict was searched. Raw datasets and upstream GitHub checkout folders, model weights and runtime environments were excluded. Full text streams were read without the earlier 8MB file/2MB archive-member cap; experiment ZIP/TAR members were inspected without extracting into historical directories. Binary files were indexed by metadata, not executed or deserialized. No inference, scoring, new scientific statistics or GPU work occurred.

Final pass: {S['files']} files; {S['fully_streamed_text_files']} fully streamed text files; {S['archives']} project experiment archives; {S['execution_candidates_including_duplicates']} execution-field candidate files/members before scientific classification. Errors={len(S['errors'])}. See exact exclusions and coverage in FULL_EXPERIMENT_SCAN_SUMMARY.json.

Supplement: {len(SUP['files'])} project-owned code/data and notebook-checkpoint files were separately checked so generic data-directory exclusions do not omit project code. These contain historical code/navigation copies, not additional inference outputs. See OWN_CODE_AND_CHECKPOINT_SUPPLEMENT.json.

## Important recovered completed experiment
MCR Native V1 actually completed 4000 model generations on the same 1000 source IDs in four conditions: neutral, faithful, adversarial, irrelevant, each 1000. This is not a plan or upstream dataset. Raw model output saved for all4000; parse OK3995 and parse fail5. Raw SHA {M['sha256']}; runner SHA {M['runner_sha256']}. The runner creates user content=[audio,source_text]; manifest has the frozen native text conditions. Three conditions beyond adversarial therefore have genuine historical completed output. Prior report's controlled-only wording understated this available evidence and is superseded for general MCR historical coverage. Native and controlled are different protocols and cannot be pooled as equivalent interventions.

## Documentation coverage is incomplete
54 on-disk experimental JSONL files were indexed;40 contain actual execution/raw/failure evidence;33 distinct byte artifacts after deduplication.30 filenames are not explicitly named in AGENTS plus PROJECT_STATE/FILE_MAP/DECISIONS. This is a file-level documentation gap, not30 new scientific experiments. Formal runs can be described in docs without naming their exact raw JSONL. Many unlisted records are technical gates, unsuccessful attempts or duplicate exports.

Concrete examples include LISTEN V3/V4 six-trial gates; MCR native8-trial gate and4000-row full; MCR controlled V1/V2/V3 gates; CA-MER native6 technical records with parser failures and controlled V1–V4 gates; EmotionTalk pre-measurement attempts, pairwise gates and failed full attempt2132 records; successful Phase2 Attempt0022132; original Phase14500;8 cross-regime smoke records. Their actual statuses, source paths, hashes, duplicates and docs mention flags are in RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv.

## Claimed-but-missing paths
316 navigation references were checked;311 resolve. The5 apparent failures are generic prose such as code/config/protocol and results/logs/artifacts mistakenly recognized as literal file paths. No genuine missing concrete file was established among these references. Existing paths do not alone establish claimed execution. Old missing/BLOCKED statements must be read with their dated later updates: B3 measured artifacts and corrected amendment assets exist; old missing-state entries remain historical.

## LISTEN and other unresolved experiments
LISTEN T_THEN_A execution candidates found in full file/archive pass={len(reverse)}. The sole LISTEN-named T_THEN_A text mention says the native gate does NOT add MCR reverse-order arms; it is not a run declaration. Source/plan/execution/archived-copy levels remain distinct. V3/V4 3C input is audio then text, and 3A/3B correctness did not filter3C. No additional completed LISTEN correctness-gated reverse protocol was identified. NOT_FOUND_IN_ACCESSIBLE_STORAGE is scoped evidence, not proof of never having run.

CA-MER existing6000 resource-sweep rows retain technical run identity. Actual A_ONLY/V_ONLY labels exist, and independent B3 seven-class score vectors exist; no verified16-class vector execution was recovered. Unpublished candidate score assets are not assumed from field names.

## Docs maintenance
User explicitly authorized docs updates after the previous read-only forensics. Only docs/PROJECT_STATE.md, docs/FILE_MAP.md and docs/DECISIONS.md are appended; AGENTS itself remains unchanged. Existing dated content preserved. All scientific outputs, protocols, media and model files remain unchanged. New conclusions stay RETROSPECTIVE_EVIDENCE_RECOVERY; frozen populations are not pooled or recomputed.
'''
(O/'FULL_EXPERIMENT_RECOVERY_REPORT.md').write_text(report,encoding='utf-8')
# Backup and append only the three expressly authorized navigation documents.
backup=O/'docs_before_update';backup.mkdir();changes=[]
for name in ['PROJECT_STATE.md','FILE_MAP.md','DECISIONS.md']:
 p=R/'docs'/name;before=p.read_bytes();shutil.copyfile(p,backup/name)
 if name=='PROJECT_STATE.md':
  add=f'''\n\n## Retrospective experiment evidence recovery — 2026-10-10\n\n- Label: RETROSPECTIVE_EVIDENCE_RECOVERY. Navigation docs are references, not an exhaustive experiment ledger.\n- Full project-local pass excludes raw datasets/upstream checkout/model/environment folders: {S['files']} files, {S['fully_streamed_text_files']} streamed text files, {S['archives']} experiment archives.\n- VERIFIED EXECUTION: MCR Native V1 has4000 successful generations, neutral/faithful/adversarial/irrelevant each1000 on the same1000 items; parser OK3995/fail5. This historical native evidence is separate from controlled V3.\n- VERIFIED DOCUMENTATION GAP:40 execution-evidence JSONL files,33 unique byte artifacts;30 filenames not explicitly named in core navigation docs. Gates/failures/copies are not additional formal completed experiments.\n- SCOPED NOT FOUND: no additional LISTEN T_THEN_A raw execution or correctness-gated3C run recovered. V3/V4 existing outputs remain intact;378 conflict3C samples are not a DualReadable pool.\n- Existing CA-MER single-modality labels and independent7-class B3 scores are recoverable;16-class scores remain unverified/not recovered.\n- Canonical private recovery report and registers: /root/autodl-tmp/affective-conflict-forensics-expanded-v1/FULL_EXPERIMENT_RECOVERY_REPORT.md and RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv. No new GPU/model run, no frozen-result recomputation, no GitHub changes.\n'''
 elif name=='FILE_MAP.md':
  add='''\n\n## Experiment evidence recovery navigation — 2026-10-10\n\nAll additions below are RETROSPECTIVE_EVIDENCE_RECOVERY; historical result files remain unchanged.\n- audit/QWEN25_MCR_NATIVE_V1/full_run/qwen25_mcr_native_full_v1.jsonl — actual4000 native generations, four text conditions ×1000; SHA e20ede77e563d4bb5ae29c4b6f57308bd06c736dd4344e318e7acf560b0c6b77.\n- code/run_qwen25_mcr_native_v1.py — native input construction, inspected only; SHA6848b469eb15e51b068262afb5d3c7899793d8910e08b842ce4c9e6c42a1ea7b.\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv — all54 reviewed experimental JSONL paths, actual states, hashes, duplication and core-doc mention flags.\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/DOC_REFERENCE_RECONCILIATION.csv —316 referenced path checks; generic prose false matches identified.\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/FULL_EXPERIMENT_RECOVERY_REPORT.md — verified completed runs vs technical gates/failures/plans/copies; scoped residual gaps.\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/FULL_EXPERIMENT_SCAN_SUMMARY.json and FULL_EXPERIMENT_FILE_INVENTORY.json — exact project-local scan coverage/exclusions; full text streams and archive members inspected, binary metadata only.\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/MCR_NATIVE_FOUR_CONDITION_RECOVERY.json — same1000-item intersection, original row examples and read-only historical source excerpts.\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/docs_before_update/ — original three navigation docs before user-authorized append.\n'''
 else:
  numbers=[int(x) for x in re.findall(r'##\s+D-(\d+)',before.decode(errors='replace'))];nextid=max(numbers,default=0)+1
  add=f'''\n\n## D-{nextid:03d} — Distinguish undocumented execution evidence from new scientific experiments (2026-10-10)\n\nUser explicitly authorized a full scan only under /root/autodl-tmp/affective-conflict, skipping raw datasets/upstream checkout/model/environment folders, and updates to AGENTS-referenced docs. All new findings are RETROSPECTIVE_EVIDENCE_RECOVERY.\n\nDecision: do not infer non-execution from missing AGENTS/core-doc entries. Use actual output rows, input construction, hashes and run-specific protocol. Conversely, absent filename mentions do not prove an experiment entirely undocumented, and repeated copies/gates/failed attempts do not count as independent formal completed experiments.\n\nVerified correction: MCR Native V1 includes actual neutral/faithful/adversarial/irrelevant outputs,1000 each on the same1000 IDs,4000 generation successes,3995 parse successes and5 parse failures. Preserve native/controlled protocol distinction. The general historical evidence statement must acknowledge the other completed native text conditions.\n\nLISTEN reverse-order execution and correctness-gated native3C remain NOT_FOUND_IN_ACCESSIBLE_STORAGE after the expanded project-local file/archive scan. This is not proof of historical nonexistence. No new GPU/model execution or scientific statistics were performed.\n\nOnly navigation docs appended under this authorization; frozen manifests/protocols/results and raw assets unchanged. Recovery report and ledger: /root/autodl-tmp/affective-conflict-forensics-expanded-v1/. Old dated missing-state records are preserved rather than rewritten.\n'''
 if name=='PROJECT_STATE.md':
  add+=f'\n- Supplementary coverage: {len(SUP["files"])} project-owned code/data and notebook-checkpoint files separately checked; no additional inference output recovered.\n'
 if name=='FILE_MAP.md':
  add+='\n- /root/autodl-tmp/affective-conflict-forensics-expanded-v1/OWN_CODE_AND_CHECKPOINT_SUPPLEMENT.json — project-owned code/data and checkpoint supplement, 10 files.\n'
 after=before+add.encode('utf-8');assert after.startswith(before);p.write_bytes(after)
 changes.append({'path':str(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'original_prefix_preserved':True,'backup':str(backup/name)})
(O/'DOC_UPDATE_PROVENANCE.json').write_text(json.dumps({'label':'RETROSPECTIVE_EVIDENCE_RECOVERY','authorization':'User explicitly requested full project-local scan and update AGENTS-referenced docs on2026-10-10','changes':changes,'AGENTS_modified':False,'scientific_files_modified':False},indent=2))
with open(O/'OUTPUT_SHA256SUMS.txt','x') as f:
 for p in sorted(O.iterdir()):
  if p.is_file() and p.name!='OUTPUT_SHA256SUMS.txt' and not p.name.endswith('.transfer'):f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n')
print('EXPANDED_FINALIZED_DOCS_UPDATED',len(changes),'LISTEN_REVERSE',len(reverse))
