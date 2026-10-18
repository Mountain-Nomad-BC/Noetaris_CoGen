"""Validate supported Compose targets before deployment."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    'baseline': ['compose.yaml'],
    'ocr': ['compose.yaml', 'deploy/local/compose.ocr.yaml'],
    'semantic': ['compose.yaml', 'deploy/local/compose.semantic.yaml'],
    'cpu': ['compose.yaml', 'deploy/local/compose.cpu.yaml'],
    'edge': ['compose.yaml', 'deploy/local/compose.edge.yaml'],
    'noetaris': ['compose.yaml', 'deploy/local/compose.noetaris.yaml'],
    'amd': ['compose.yaml', 'deploy/amd/compose.amd.yaml'],
}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=sorted(TARGETS))
    args = parser.parse_args(argv)
    files = TARGETS[args.target]
    command = ['docker', 'compose']
    for item in files:
        command.extend(['-f', item])
    command.append('config')
    env = os.environ.copy()
    result = subprocess.run(command, cwd=ROOT, env=env, text=True)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
