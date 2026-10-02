"""Build and verify an isolated, test-signed EXE; never uses release keys."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    import tempfile
    (ROOT / "build").mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="smoke-", dir=ROOT / "build"))
    for name in ("app.py", "VERSION.txt", "PelicanWorkbench.spec"):
        shutil.copy2(ROOT / name, stage / name)
    for name in ("web", "workbench", "security"):
        shutil.copytree(ROOT / name, stage / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "public_key.py", "release_manifest.*"))
    def run(*args):
        subprocess.run(args, cwd=stage, check=True, env={**os.environ, "PYTHONUTF8": "1", "PELICAN_SELF_TEST_REPORT": str(stage / "self-test.json")})
    run(sys.executable, str(ROOT / "tools/sign_release.py"), "--root", str(stage), "--version", (stage / "VERSION.txt").read_text().strip(), "--private-key", str(stage / "test-only.key"))
    run(sys.executable, "-c", "from pathlib import Path; from security.runtime_verify import verify_release_integrity; ok, reason = verify_release_integrity(Path('.')); assert ok, reason; print('Signed resources: PASS')")
    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "PelicanWorkbench.spec")
    run(str(stage / "dist/PelicanWorkbench.exe"), "--self-test")
    print("Packaged EXE self-test: PASS")
    print("Test-signed artifact (not for release):", stage / "dist/PelicanWorkbench.exe")

if __name__ == "__main__":
    main()
