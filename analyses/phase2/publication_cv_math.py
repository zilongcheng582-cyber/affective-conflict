"""PATCHED_IMPLEMENTATION: same historical design/fit/metric; corrected shared folds only."""
import numpy as np
from scipy.special import expit
from scipy.stats import rankdata
SEED=20260928

def grouped_fold_map(group_ids, seed=SEED, n_splits=5):
    groups = np.asarray(sorted(set(group_ids)), dtype=object)
    if len(groups) < n_splits: raise ValueError('fewer groups than folds')
    groups = groups[np.random.default_rng(seed).permutation(len(groups))]
    return {group: fold_id for fold_id, fold in enumerate(np.array_split(groups, n_splits)) for group in fold.tolist()}

def design(rows,fs):
 cols=[np.ones(len(rows)),np.array([r["pair"]=="AV" for r in rows],float),np.array([r["pair"]=="VT" for r in rows],float)]
 names=["intercept_AT","pair_AV","pair_VT"]
 for f in fs:
  if f=="src":cols.append(np.array([r["_srcz"] for r in rows]));names.append("delta_source_label_probability_per_SD")
  if f=="mar":cols.append(np.array([r["_marz"] for r in rows]));names.append("delta_top1_top2_margin_per_SD")
  if f=="ent":cols.append(np.array([r["_entz"] for r in rows]));names.append("delta_normalized_entropy_per_SD")
  if f=="ord":cols.append(np.array([r["_order"] for r in rows]));names.append("FIRST_IS_MODALITY1")
 return np.column_stack(cols),names

def fit(X,y,w=None):
 X=np.asarray(X,float);y=np.asarray(y,float);w=np.ones(len(y)) if w is None else np.asarray(w,float);keep=w>0;X=X[keep];y=y[keep];w=w[keep]
 b=np.zeros(X.shape[1]);ok=False;it=0
 def ll(b):
  z=np.clip(X@b,-35,35);return float(np.sum(w*(y*z-np.logaddexp(0,z))))
 for it in range(1,101):
  z=np.clip(X@b,-35,35);p=expit(z);g=X.T@(w*(y-p));H=X.T@((w*p*(1-p))[:,None]*X)
  try:d=np.linalg.solve(H,g)
  except:break
  mx=np.max(np.abs(d))
  if mx>8:d*=8/mx
  old=ll(b);step=1.;good=False
  for _ in range(40):
   cand=b+step*d
   if ll(cand)>=old-1e-12:good=True;break
   step*=.5
  if not good:
   if np.max(np.abs(g))<1e-6:ok=True
   break
  b=cand
  if np.max(np.abs(step*d))<1e-8:
   if np.max(np.abs(X.T@(w*(y-expit(np.clip(X@b,-35,35))))))<1e-5:ok=True
   break
 z=np.clip(X@b,-35,35);p=expit(z);H=X.T@((w*p*(1-p))[:,None]*X)
 try:bread=np.linalg.inv(H);cond=float(np.linalg.cond(H))
 except:bread=None;cond=None
 return {"b":b,"p":p,"ll":ll(b),"ok":ok,"it":it,"bread":bread,"cond":cond,"X":X,"y":y,"w":w}

def metric(y,p):
 y=np.asarray(y,int);p=np.clip(np.asarray(p,float),1e-12,1-1e-12);pos=sum(y==1);neg=sum(y==0);bal=auc=None
 if pos and neg:
  yh=p>=.5;bal=float((np.mean(yh[y==1])+np.mean(~yh[y==0]))/2)
  rk=rankdata(p);auc=float((rk[y==1].sum()-pos*(pos+1)/2)/(pos*neg))
 return {"log_loss":float(np.mean(-(y*np.log(p)+(1-y)*np.log(1-p)))),"balanced_accuracy":bal,"AUROC":auc,"Brier_score":float(np.mean((p-y)**2))}
