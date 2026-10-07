"""This is a validated post-hoc reconstruction implementation.
 It is not claimed to be the original historical producer.
 Scientific raw-prefix statements are retained from the validated original builder.
 """
import argparse,csv,json
from pathlib import Path
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    from collections import Counter,defaultdict
    from datetime import datetime,timezone
    import csv,hashlib,json,math,random,subprocess
    import numpy as np
    R=a.root.resolve()
    O=a.output
    D=R/"data/EmotionTalk/extracted"
    G=R/"external/EmotionTalk"
    NP=G/"EmotionTalk/dataset/mm-process"
    L=["angry","disgusted","fearful","happy","neutral","sad","surprised"]
    P=["ALL_SAME","T=A!=V","T=V!=A","A=V!=T","ALL_DIFFERENT"]
    S={"train":15413,"val":1908,"test":1929}
    EP={"ALL_SAME":5235,"T=A!=V":3701,"T=V!=A":1599,"A=V!=T":5700,"ALL_DIFFERENT":3015}
    EPAIR={"AV":{"valid":19250,"conflict":8315,"consistent":10935},"AT":{"valid":19250,"conflict":10314,"consistent":8936},"VT":{"valid":19250,"conflict":12416,"consistent":6834}}
    def pattern(t,a,v):
     if t==a==v:return P[0]
     if t==a:return P[1]
     if t==v:return P[2]
     if a==v:return P[3]
     return P[4]
    folders={"T":"Text","A":"Audio","V":"Video","M":"Multimodal"}
    ann={}
    rels={}
    counts={}
    for m,f in folders.items():
     base=D/f/"json";fs=sorted(base.rglob("*.json"));counts[m]=len(fs)
     if len(fs)!=19250:raise SystemExit("Annotation count mismatch "+m)
     ann[m]={};rels[m]={}
     for p in fs:
      u=p.stem
      if u in ann[m]:raise SystemExit("Duplicate ID "+u)
      x=json.loads(p.read_text(encoding="utf-8"))
      if x.get("emotion_result") not in L:raise SystemExit("Unexpected source label "+repr(x.get("emotion_result")))
      ann[m][u]=x;rels[m][u]=p.relative_to(base)
    ids=sorted(ann["T"])
    if len(ids)!=19250 or any(set(ann[m])!=set(ids) for m in folders):raise SystemExit("Canonical T/A/V/M alignment failed.")
    archives={"T":"txt_label.npz","A":"audio_label.npz","V":"video_label.npz","M":"mm_label.npz"}
    sm={}
    sc={}
    for m,n in archives.items():
     mp={};cc={}
     with np.load(NP/n,allow_pickle=True) as z:
      for k,s in [("train_corpus","train"),("val_corpus","val"),("test_corpus","test")]:
       d=z[k].item()
       if not isinstance(d,dict):raise SystemExit("Invalid split object "+n)
       cc[s]=len(d)
       for u in d:
        if u in mp:raise SystemExit("Duplicate split ID "+u)
        mp[u]=s
     if cc!=S or set(mp)!=set(ids):raise SystemExit("Official split mismatch "+n)
     sm[m]=mp;sc[m]=cc
    if any(sm[m]!=sm["T"] for m in folders):raise SystemExit("NPZ split membership differs.")
    rows={}
    full=Counter()
    fp={p:Counter() for p in ("AV","AT","VT")}
    spbad=0
    for u in ids:
     y={m:ann[m][u]["emotion_result"] for m in folders};pt=pattern(y["T"],y["A"],y["V"]);full[pt]+=1
     for p,a,b in [("AV","A","V"),("AT","A","T"),("VT","V","T")]:
      fp[p]["valid"]+=1;fp[p]["conflict" if y[a]!=y[b] else "consistent"]+=1
     sv=[None if ann[m][u].get("speaker_id") is None else str(ann[m][u]["speaker_id"]) for m in ("T","A","V","M")]
     if len({x for x in sv if x is not None})>1:spbad+=1
     rows[u]={"utterance_id":u,"speaker_id":sv[0] or "","text":str(ann["T"][u].get("content","")),
     "text_emotion":y["T"],"audio_emotion":y["A"],"video_emotion":y["V"],"multimodal_emotion":y["M"],"trimodal_pattern":pt,
     "av_relation":"CONFLICT" if y["A"]!=y["V"] else "CONSISTENT","at_relation":"CONFLICT" if y["A"]!=y["T"] else "CONSISTENT","vt_relation":"CONFLICT" if y["V"]!=y["T"] else "CONSISTENT",
     "audio_path":(D/"Audio/wav"/rels["A"][u].with_suffix(".wav")).resolve().as_posix(),
     "video_path":(D/"Multimodal/mp4"/rels["V"][u].with_suffix(".mp4")).resolve().as_posix(),
     "video_path_role":"original_AV_container_for_silent_derivation_only","official_split":sm["T"][u],"_tuple":(y["T"],y["A"],y["V"])}
    if dict(full)!=EP or spbad:raise SystemExit("Full pattern pool or direct speaker ID consistency failed.")
    for p,e in EPAIR.items():
     if {k:fp[p][k] for k in ("valid","conflict","consistent")}!=e:raise SystemExit("Full pair pool mismatch "+p)
    rng=random.Random(42)
    pool={p:defaultdict(list) for p in P}
    for u in ids:pool[rows[u]["trimodal_pattern"]][rows[u]["_tuple"]].append(u)
    selected=[]
    allocation={}
    for p in P:
     d=pool[p];keys=sorted(d)
     if len(keys)>300:raise SystemExit("Too many tuples for quota "+p)
     for k in keys:d[k].sort();rng.shuffle(d[k])
     cap={k:len(d[k]) for k in keys};q={k:1 for k in keys};left=300-len(keys)
     if sum(cap.values())<300:raise SystemExit("Insufficient pool "+p)
     while left:
      active={k:cap[k]-q[k] for k in keys if q[k]<cap[k]};tot=sum(active.values())
      if not tot:raise SystemExit("Insufficient residual capacity "+p)
      ideal={k:left*v/tot for k,v in active.items()};grant={k:min(active[k],math.floor(ideal[k])) for k in active};used=sum(grant.values())
      for k,n in grant.items():q[k]+=n
      left-=used
      if left:
       order=sorted((k for k in active if q[k]<cap[k]),key=lambda k:(-(ideal[k]-math.floor(ideal[k])),k))
       for k in order:
        if not left:break
        if q[k]<cap[k]:q[k]+=1;left-=1
     details=[];part=[]
     for k in keys:
      chosen=d[k][:q[k]];part+=chosen;details.append({"tuple_T_A_V":list(k),"pool_n":cap[k],"selected_n":q[k],"selected_ids":sorted(chosen)})
     if len(part)!=300:raise SystemExit("Pattern quota failed "+p)
     selected+=part;allocation[p]={"pool_n":sum(cap.values()),"selected_n":len(part),"tuple_strata":len(keys),"tuple_allocations":details}
    selected=sorted(selected)
    if len(selected)!=1500 or len(set(selected))!=1500:raise SystemExit("Panel is not 1500 unique IDs.")
    seq=[]
    for family,base in [("cyclic",L),("reversed_cyclic",list(reversed(L)))]:
     for i in range(7):
      q=base[i:]+base[:i];seq.append({"candidate_sequence_id":f"CS{len(seq)+1:02d}","family":family,"rotation_index":i,"labels":q,"pipe":"|".join(q)})
    schedule=[i for i in range(14) for _ in range(107)]+[0,1]
    random.Random(42).shuffle(schedule)
    panel=[]
    for u,i in zip(selected,schedule):
     x=dict(rows[u]);x["candidate_sequence_id"]=seq[i]["candidate_sequence_id"];x["candidate_sequence"]=seq[i]["pipe"];panel.append(x)
    cols=['utterance_id', 'speaker_id', 'text', 'text_emotion', 'audio_emotion', 'video_emotion', 'multimodal_emotion', 'trimodal_pattern', 'av_relation', 'at_relation', 'vt_relation', 'audio_path', 'video_path', 'candidate_sequence_id', 'candidate_sequence', 'official_split', 'video_path_role']
    with (a.output/'master_panel.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(panel)
    with (a.output/'canonical.csv').open('x',encoding='utf-8',newline='') as f:
        cc=[k for k in cols if k not in ['candidate_sequence_id','candidate_sequence']];w=csv.DictWriter(f,fieldnames=cc,extrasaction='ignore');w.writeheader();w.writerows(rows[u] for u in ids)
    print(json.dumps({'canonical_N':len(rows),'panel_N':len(panel),'model_execution':False}))
if __name__=='__main__':main()
