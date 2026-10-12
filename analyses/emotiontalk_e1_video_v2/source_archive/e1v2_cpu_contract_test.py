"""Synthetic CPU statistic contract test, isolated from scientific records."""
import ast,pathlib,numpy as np,json
def extract(path,name,namespace):
 tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace);return namespace[name]
base=pathlib.Path(__file__).parent
stats=extract(base/'e1v2_analysis.py','stats',{'np':np});ind=extract(base/'e1v2_verify.py','independent_stats',{'np':np});holm=extract(base/'e1v2_analysis.py','holm',{})
d=np.zeros(146);d[:30]=-.5;d[30:40]=.5;clusters=[f'D{i if i<134 else i-134:03d}' for i in range(146)];a=stats(d,clusters,2026101203);b=ind(d.tolist(),clusters,2026101203)
mapping={'effect':'effect','utterance_ci95':'utterance_ci95','dialogue_cluster_ci95':'dialogue_cluster_ci95','p_two_sided':'p_two_sided'};checks={}
for k,v in mapping.items():checks[k]=float(np.max(abs(np.asarray(a[k])-np.asarray(b[v]))));assert checks[k]<=1e-12
assert abs(a['effect']-(-10/146))<=1e-12 and a['clusters']==134
rs=[{'p_two_sided':v} for v in [.04,.001,.02]];holm(rs);assert all(abs(r['p_holm']-expected)<1e-12 for r,expected in zip(rs,[.04,.003,.04]))
zero=stats(np.zeros(146),clusters,2026101204);assert zero['p_two_sided']==1 and zero['utterance_ci95']==[0.,0.]
assert a==stats(d,clusters,2026101203)
receipt={'status':'PASS','role':'SYNTHETIC_CPU_TEST_NOT_PILOT_NOT_FORMAL','checks':['146-item known effect','134 clusters','independent item and cluster CI agreement','independent paired signflip agreement','Holm family correction','zero effect and ties','deterministic repeated results'],'max_statistic_errors':checks,'GPU_used':False}
(base/'CPU_STATISTIC_CONTRACT_TEST.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
