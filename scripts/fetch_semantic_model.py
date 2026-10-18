"""Explicit, bounded acquisition of one pinned CPU encoder; never run on import."""
from pathlib import Path
import hashlib
import os
import json
import urllib.request
import argparse

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
FILES = {'model.onnx': 'onnx/model.onnx', 'tokenizer.json': 'tokenizer.json',
         'config.json': 'config.json', 'tokenizer_config.json': 'tokenizer_config.json', 'README.md': 'README.md'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if not args.download:
        parser.error('Explicit --download required')
    destination = ROOT / 'state/models/all-MiniLM-L6-v2'
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, remote in FILES.items():
        target = destination / name
        if target.is_symlink():
            raise ValueError('Model links are not admitted')
        if not target.exists():
            request = urllib.request.Request(f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{remote}',
                                             headers={'User-Agent': 'NSAI-local-research-ingestion/1.0'})
            temporary = target.with_suffix(target.suffix + '.partial')
            size = 0
            owned_partial = False
            try:
                # Reserve our scratch file before network access. An earlier
                # interrupted download belongs to its creator and is preserved.
                with temporary.open('xb') as output:
                    owned_partial = True
                    with urllib.request.urlopen(request, timeout=60) as response:
                        while block := response.read(65536):
                            size += len(block)
                            if size > 100 * 1024 * 1024:
                                raise ValueError('Model file exceeds budget')
                            output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
                # Atomic exclusive publication also preserves a target created
                # by a concurrent downloader on platforms where rename replaces.
                os.link(temporary, target)
            finally:
                if owned_partial and temporary.exists():
                    temporary.unlink()
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = dict(model_id=MODEL, revision=REVISION, dimension=384, max_sequence_length=256,
                    files=hashes, license='apache-2.0', source=f'https://huggingface.co/{MODEL}/tree/{REVISION}',
                    trust='HTTPS pinned-revision acquisition; local hashes are custody, not publisher signatures')
    target = destination / 'manifest.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8')) != manifest:
            raise ValueError('Existing encoder manifest mismatch')
    else:
        with target.open('x', encoding='utf-8') as output:
            json.dump(manifest, output, indent=2)
    print(json.dumps(dict(status='ACQUIRED', model=MODEL, revision=REVISION, bytes=sum((destination/n).stat().st_size for n in FILES))))


if __name__ == '__main__':
    main()
