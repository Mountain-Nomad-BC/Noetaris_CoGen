"""Keep all retained scanner findings visible, including severity/fix status."""
from pathlib import Path
from collections import Counter
import json


def main():
    ROOT=Path(__file__).resolve().parents[1]
    reports={}
    for name,filename in [('api','api-image-cves-final.sarif'),('cpu-model','cpu-image-cves.sarif'),('database','db-image-cves.sarif')]:
        path=ROOT/'evidence/raw'/filename
        if not path.exists():reports[name]={'status':'PENDING'};continue
        data=json.loads(path.read_text())
        rules=[r for run in data.get('runs',[]) for r in run.get('tool',{}).get('driver',{}).get('rules',[])]
        severity=Counter(r.get('properties',{}).get('cvssV3_severity','UNSPECIFIED') for r in rules)
        fixable=[r for r in rules if r.get('properties',{}).get('fixed_version') not in (None,'','not fixed')]
        reports[name]=dict(status='FINDINGS_RETAINED',unique_advisories=len(rules),severity=dict(severity),
            fixable_advisories=len(fixable),fixable_high_critical=sum(r.get('properties',{}).get('cvssV3_severity') in {'HIGH','CRITICAL'} for r in fixable),
            source=filename,not_zero_vulnerability_assurance=True)
    report=dict(reports=reports,public_production_clearance=False,
        limitation='Scanner-reported OS advisories remain visible; no comprehensive exploitability assessment claimed')
    (ROOT/'evidence/raw/image-scan-summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
