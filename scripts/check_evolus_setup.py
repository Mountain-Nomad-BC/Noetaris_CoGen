"""Validate local Evolus bindings without remote execution or secret output."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.integrations.configuration import evolus_setup


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='')
    parser.add_argument('--key-file',default=str(ROOT/'secrets/evolus_api_key.txt'))
    args=parser.parse_args()
    result=evolus_setup(args.config,args.key_file)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['configuration_ready'] else 2)
