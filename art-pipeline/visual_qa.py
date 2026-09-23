from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
GENERATED = ROOT / "art-work" / "generated"
QA = ROOT / "art-work" / "qa"

ALLOWED = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in manifest["assets"]}
    QA.mkdir(parents=True, exist_ok=True)

    results = []
    for path in sorted(GENERATED.iterdir()) if GENERATED.exists() else []:
        if path.suffix.lower() not in ALLOWED:
            continue
        asset_id = path.stem
        asset = assets.get(asset_id)
        checks = {"exists": True, "format": path.suffix.lower() in ALLOWED}
        errors = []

        try:
            with Image.open(path) as im:
                checks["integrity"] = im.verify() is None
            with Image.open(path) as im:
                checks["width"] = im.width
                checks["height"] = im.height
                checks["mode"] = im.mode
                checks["alpha"] = "A" in im.getbands()
                if im.width < 512 or im.height < 512:
                    errors.append("image is smaller than 512px on one side")
                if path.stat().st_size < 20_000:
                    errors.append("file is suspiciously small")
        except Exception as exc:
            checks["integrity"] = False
            errors.append(str(exc))

        passed = bool(checks.get("integrity")) and not errors
        result = {
            "asset_id": asset_id,
            "key": asset["key"] if asset else None,
            "priority": asset["priority"] if asset else None,
            "passed": passed,
            "errors": errors,
            "checks": checks,
        }
        results.append(result)
        print(("PASS" if passed else "FAIL"), asset_id, "; ".join(errors))

    report = QA / "visual-qa.json"
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {report}")


if __name__ == "__main__":
    main()
