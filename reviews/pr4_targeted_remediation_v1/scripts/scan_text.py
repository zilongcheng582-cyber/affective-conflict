import json,csv,subprocess,sys,re,os,collections
csv.field_size_limit(10**9)
os.chdir(sys.argv[1])
files=subprocess.check_output(['git','diff','--name-only','544ca0e','HEAD']).decode().split()
main=[]
for p in subprocess.check_output(['git','ls-tree','-r','--name-only','544ca0e']).decode().split():
    if p.endswith(('.csv','.json','.jsonl','.md','.py','.txt')):
        main.append(subprocess.check_output(['git','show','544ca0e:'+p]).decode('utf-8','replace'))
corpus='\n'.join(main)
def leaves(f):
    if f.endswith('.json'):
        def walk(o,p):
            if isinstance(o,dict):
                for k,v in o.items(): yield from walk(v,p+'/'+str(k))
            elif isinstance(o,list):
                for v in o: yield from walk(v,p+'/[]')
            elif isinstance(o,str): yield p,o
        yield from walk(json.load(open(f,encoding='utf-8')),'')
    elif f.endswith('.csv'):
        for r in csv.DictReader(open(f,newline='',encoding='utf-8-sig')):
            for k,v in r.items():
                if isinstance(v,str): yield '/'+str(k),v
nl=re.compile(r'[A-Za-z]{2,}(?:\s+[A-Za-z,.\'!?-]{1,}){7,}')
res=collections.defaultdict(lambda: collections.Counter())
for f in files:
    if not f.endswith(('.json','.csv')): continue
    for p,v in leaves(f):
        if len(v)<50 or v.startswith('/') or not nl.search(v): continue
        # skip strings authored by the analysis (heuristic: contains our vocabulary)
        inmain = v in corpus
        key=re.sub(r'\[\]','[]',p)
        res[(f,key)]['in_main' if inmain else 'not_in_main']+=1
for (f,k),c in sorted(res.items()):
    print(c['in_main'],c['not_in_main'],f,k)
