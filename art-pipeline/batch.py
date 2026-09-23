from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(script: str, *args: str) -> None:
    cmd = [PY, str(ROOT / "art-pipeline" / script), *args]
    print("\n>>>", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Pelican Workbench art pipeline")
    parser.add_argument("--ids", required=True, help="comma-separated asset IDs")
    parser.add_argument("--skip-generate", action="store_true")
    args = parser.parse_args()

    run("asset_scanner.py")
    run("prompt_builder.py", "--ids", args.ids)
    if not args.skip_generate:
        run("generator.py", "--ids", args.ids)
    run("visual_qa.py")
    run("consistency_check.py")

    print("\nPipeline stopped before human review.")
    print("Run: python art-pipeline\\review_server.py")
    print("After review: python art-pipeline\\integrate.py")


if __name__ == "__main__":
    main()
