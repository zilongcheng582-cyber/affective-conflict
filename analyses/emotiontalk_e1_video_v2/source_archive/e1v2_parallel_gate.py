import os,sys,subprocess,json,traceback
from e1v2_cpu_gate import ROOT,prepare,gate,dump
try:
 prepare();jobs=[]
 for i in range(4):
  f=open(ROOT/'logs'/f'CPU_WORKER_{i}.log','ab');env=dict(os.environ,E1V2_CPU_WORKER=str(i),E1V2_CPU_WORKERS='4',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
  q=subprocess.Popen([sys.executable,'-B',str(ROOT/'code/e1v2_cpu_gate.py')],env=env,stdout=f,stderr=subprocess.STDOUT);jobs.append((i,q,f))
 dump(ROOT/'logs/CPU_PARALLEL_PIDS.json',{str(i):q.pid for i,q,f in jobs})
 codes={str(i):q.wait() for i,q,f in jobs};[f.close() for i,q,f in jobs]
 dump(ROOT/'logs/CPU_PARALLEL_EXIT_CODES.json',codes);assert not any(codes.values()),codes
 assert len(list((ROOT/'02_media/receipts').glob('*.json')))==146
 gate();print('PARALLEL_CPU_GATE_PASS',flush=True)
except Exception as e:
 dump(ROOT/'01_design/CPU_MEDIA_GATE.json',{'status':'FAIL','error':repr(e),'traceback':traceback.format_exc(),'GPU_executed':False});raise
