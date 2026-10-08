"""Independently join recovered Phase2/Phase3 responses against the frozen plan."""
import argparse,json
from src.common.runtime import REPO,verify_release
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');p.parse_args();verify_release()
    from analyses.post_audit.replay import verify_evidence,verify_evidence_anchors,reconstruct_source,verify_phase3,csvrows,jsonrows
    anchors=verify_evidence_anchors()
    verify_evidence()
    _,phase2=reconstruct_source()
    rows=verify_phase3(csvrows(REPO/'manifests/emotiontalk/trimodal_plan.csv'),
                       jsonrows(REPO/'evidence/emotiontalk/phase3_observed_outputs.jsonl'),phase2)
    r={'scientific_role':'TWO_VS_ONE_PAIRWISE_TO_TRIMODAL_CONSISTENCY',
       'analysis_origin':'POST_AUDIT_REANALYSIS','planned':len(rows),
       'resolved':sum(x['prediction_resolved'] for x in rows),
       'correct':sum(x['match_indicator'] or 0 for x in rows),
       'unresolved':sum(not x['prediction_resolved'] for x in rows),
       'PHASE3_PROJECTION_BINDING':anchors['PHASE3_PROJECTION_BINDING'],
       'PHASE3_PREEXISTING_ANCHOR':anchors['PHASE3_PREEXISTING_ANCHOR']}
    if (r['planned'],r['resolved'],r['correct'],r['unresolved'])!=(402,294,268,108):
        raise ValueError('Observed Phase3 identities disagree with historical report')
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
