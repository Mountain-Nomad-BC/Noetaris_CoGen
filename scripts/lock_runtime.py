"""Record resolved runtime dependency closure, excluding local verification tools."""
from importlib import metadata
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import tomllib
import urllib.request


def resolved_runtime(root, *, distribution=metadata.distribution):
    """Resolve declared runtime roots and requested extras, never test extras.

    Revisit a distribution when another parent requests a new extra. Otherwise
    traversal order can silently omit a runtime dependency such as psycopg's
    binary implementation. Reject mismatched installed versions before writing.
    """
    project=tomllib.loads((Path(root)/'pyproject.toml').read_text(encoding='utf-8'))
    pending=[Requirement(raw) for raw in project['project']['dependencies']]
    pending=[req for req in pending if req.marker is None or req.marker.evaluate({'extra':''})]
    found={};expanded={}
    while pending:
        required=pending.pop();name=canonicalize_name(required.name)
        if required.url:
            raise ValueError('Runtime lock requires named index distributions')
        dist=distribution(name)
        if required.specifier and not required.specifier.contains(dist.version,prereleases=True):
            raise ValueError(f'Installed version does not satisfy runtime requirement: {name}')
        extras={''}|set(required.extras)
        if name in expanded and extras<=expanded[name]:continue
        expanded.setdefault(name,set()).update(extras)
        found[name]=dist.version
        for raw in dist.requires or []:
            req=Requirement(raw)
            if req.marker is None or any(req.marker.evaluate({'extra':extra}) for extra in expanded[name]):
                pending.append(req)
    return found


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser();parser.add_argument('--hashes',action='store_true');args=parser.parse_args()
    found=resolved_runtime(root)
    provenance=[]
    def lock_entry(item):
        name,version=item
        line=f'{name}=={version}'
        if args.hashes:
            url=f'https://pypi.org/pypi/{name}/{version}/json'
            with urllib.request.urlopen(url,timeout=30) as response: data=json.load(response)
            hashes=sorted({file['digests']['sha256'] for file in data['urls']})
            if not hashes:raise RuntimeError(f'Missing hashes for {name}')
            provenance.append(dict(package=name,version=version,index_metadata=url,artifact_hashes=hashes))
            line+=' '+ ' '.join('--hash=sha256:'+digest for digest in hashes)
        return line
    with ThreadPoolExecutor(max_workers=4) as pool:lines=list(pool.map(lock_entry,sorted(found.items())))
    (root/'requirements.lock').write_text('# Resolved runtime closure; Python 3.12+; regenerate after dependency changes.\n'+'\n'.join(lines)+'\n')
    if args.hashes:(root/'evidence/raw/runtime-lock-provenance.json').write_text(json.dumps(sorted(provenance,key=lambda p:p['package']),indent=2))
    print(f'Locked {len(found)} runtime distributions.')


if __name__ == "__main__":
    main()
