"""Read/verify the frozen Phase3 report; never synthesize missing inferential results."""
import argparse,json
from src.common.runtime import REPO,verify_release
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');p.parse_args();verify_release()
    r=json.loads((REPO/'results/mainline_summary/phase3/EMOTIONTALK_PHASE3_SCIENTIFIC_ANALYSIS_V1_SUMMARY.json').read_text(encoding='utf-8'))
    assert r['population']['rows']==402 and r['population']['unique_utterances']==67
    assert r['primary_compositionality']['N']==294 and r['primary_compositionality']['correct_N']==268
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
