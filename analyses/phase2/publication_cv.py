"""Publication corrected CV only. Never writes historical full-source fits."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from publication_cv_math import grouped_fold_map, design, fit, metric, SEED

MODELS={'M0':[],'M1a':['src'],'M1b':['mar'],'M2a':['src','ent'],
        'M2b':['mar','ent'],'M3a':['src','ent','ord'],'M3b':['mar','ent','ord']}


def compare_models(prepared_source_rows):
    """Uses already source-scaled historical records; does not fit a scaler.

    CV-specific training folds are fitted for publication comparisons. No
    full-population source fit, transfer parameter replacement or Phase3 use.
    """
    rows=prepared_source_rows
    if not rows: raise ValueError('Prepared historical source records required')
    for row in rows:
        if row['pair'] not in ('AT','AV','VT') or row['_y'] not in (0,1):
            raise ValueError('Invalid source pair/resolved-side outcome')
        if any(not np.isfinite(row[k]) for k in ('_srcz','_marz','_entz','_order')):
            raise ValueError('Missing frozen source features')
    folds=grouped_fold_map([r['utterance_id'] for r in rows],seed=SEED,n_splits=5)
    y=np.asarray([r['_y'] for r in rows],dtype=int)
    result={}
    for name,features in MODELS.items():
        x,_=design(rows,features)
        predictions=np.full(len(rows),np.nan)
        success=0
        for fold in range(5):
            test=np.asarray([folds[r['utterance_id']]==fold for r in rows])
            fitted=fit(x[~test],y[~test])
            if not fitted['ok']: raise ValueError('CV training fold did not converge: '+name)
            success+=1
            predictions[test]=expit(np.clip(x[test]@fitted['b'],-35,35))
        result[name]={'metrics':metric(y,predictions),'successful_folds':success,
                      'fold_assignment':folds,'analysis_role':'PUBLICATION_CORRECTED_CV_ONLY'}
    return {'seed':SEED,'folds':folds,'models':result,'historical_full_source_fit_replaced':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared-source-records',type=Path,required=True)
    parser.add_argument('--input-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Publication output must be new')
    raw=args.prepared_source_records.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.input_sha256: raise ValueError('Prepared source input SHA mismatch')
    rows=json.loads(raw)
    result=compare_models(rows)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


if __name__=='__main__':main()
