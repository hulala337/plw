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
    parser = argparse.ArgumentParser(description="Pelican Workbench V3 art production batch")
    parser.add_argument("--ids", required=True)
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--review-model")
    args = parser.parse_args()

    run("asset_scanner.py")
    run("prompt_builder.py", "--ids", args.ids)
    if not args.skip_generate:
        run("generator.py", "--ids", args.ids)
    run("visual_qa.py")
    run("consistency_check.py")
    review_args = ["--ids", args.ids]
    if args.review_model:
        review_args += ["--model", args.review_model]
    run("vision_art_director.py", *review_args)
    run("production_report.py", "--ids", args.ids)

    print("\nV3 gate complete.")
    print("PASS_TO_HUMAN -> open review_server.py for human decision.")
    print("REWORK/HOLD -> revise reference/prompt and regenerate; do not integrate.")
    print("No V3 step auto-approves an asset.")

if __name__ == "__main__":
    main()
