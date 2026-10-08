import argparse,json
from src.common.runtime import REPO,verify_release
def main():
    p=argparse.ArgumentParser(description='Inspect frozen corrected zero-refit results');p.parse_args();verify_release()
    r=json.loads((REPO/'results/mainline_summary/cross_regime/B3_ZERO_REFIT_FINAL_EVALUATION_V1.json').read_text(encoding='utf-8'))
    print(json.dumps({'role':'HISTORICAL_CORRECTED_METRIC_REFERENCE',
                      'HISTORICAL_AUTHOR_INTERPRETATION':r.get('B3_FINAL_SCIENTIFIC_RULING'),
                      'SCIENTIFIC_RULING':'REQUIRES_INTERPRETATION',
                      'analyses':r['analyses']},indent=2))
if __name__=='__main__':main()
