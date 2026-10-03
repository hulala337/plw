"""Run from any directory with the project's Windows virtual environment."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(*args):
    subprocess.run(args, cwd=ROOT, check=True, env={**os.environ, "PYTHONUTF8": "1"})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-node', action='store_true')
    args = parser.parse_args()
    run(sys.executable, str(ROOT / 'tools/check_assets_encoding.py'))
    run(sys.executable, '-m', 'pip', 'check')
    run(sys.executable, '-m', 'compileall', '-q', 'app.py', 'workbench', 'security', 'art-pipeline', 'tools')
    run(sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    for script in ('p0_acceptance.py', 'p1_acceptance.py', 'p0_p1_integration.py'):
        run(sys.executable, str(ROOT / 'tools' / script))
    node = shutil.which('node') or (str(ROOT / '.tools/node.exe') if (ROOT / '.tools/node.exe').is_file() else None)
    if node:
        for path in sorted((ROOT / 'web' / 'assets').glob('*.js')):
            run(node, '--check', str(path))
    elif args.require_node:
        raise SystemExit('Node.js required for frontend validation')
    else:
        print('SKIP: Node.js unavailable; JavaScript checks run in CI', flush=True)
    run(sys.executable, 'app.py', '--self-test')

if __name__ == '__main__':
    main()
