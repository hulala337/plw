from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "art-work" / "approved"
TARGET = ROOT / "web" / "assets" / "generated-art"
MANIFEST = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
REPORT = ROOT / "art-work" / "reports" / "integration-report.json"


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    assets = {a["id"]: a for a in json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]}
    integrated = []
    skipped = []

    for src in sorted(APPROVED.glob("*")):
        if not src.is_file():
            continue
        asset_id = src.stem
        if asset_id not in assets:
            skipped.append({"file": src.name, "reason": "not in manifest"})
            continue
        target = TARGET / f"{asset_id}{src.suffix.lower()}"
        shutil.copy2(src, target)
        integrated.append({
            "asset_id": asset_id,
            "key": assets[asset_id]["key"],
            "priority": assets[asset_id]["priority"],
            "target": str(target.relative_to(ROOT)),
        })

    report = {"integrated": integrated, "skipped": skipped}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"integrated: {len(integrated)}")
    print(f"skipped: {len(skipped)}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
