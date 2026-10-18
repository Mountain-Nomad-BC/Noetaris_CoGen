"""Source candidate creation is gated by exact-member independent provenance review."""
from pathlib import Path
import json
from package_submission import ROOT,build_candidate

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--review-receipt',required=True,type=Path);parser.add_argument('--destination',required=True,type=Path);args=parser.parse_args(argv)
    try:
        review=json.loads(args.review_receipt.read_text())
        if review.get('source_provenance_reviewed') is not True:raise ValueError('Current-source provenance review is required before any source candidate archive')
        allowlist=review.get('allowlist')
        if not isinstance(allowlist,list) or not allowlist:raise ValueError('Reviewed explicit source allowlist is required')
        report=build_candidate(ROOT,args.destination,allowlist,review=review)
    except (ValueError,OSError) as error:print('FAIL:',error);return 1
    print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
