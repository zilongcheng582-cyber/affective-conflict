import argparse,json
from src.common.runtime import REPO,verify_release
def main():
    p=argparse.ArgumentParser(description='Inspect frozen corrected zero-refit results');p.parse_args();verify_release()
    r=json.loads((REPO/'results/mainline_summary/cross_regime/B3_ZERO_REFIT_FINAL_EVALUATION_V1.json').read_text(encoding='utf-8'))
    assert r['QWEN_MAINLINE_SCIENCE']=='CLOSED';print(json.dumps(r['analyses'],indent=2))
if __name__=='__main__':main()
