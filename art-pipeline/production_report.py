from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
QA = ROOT / "art-work" / "qa"
VISION = QA / "vision-review"
REPORTS = ROOT / "art-work" / "reports"

def main() -> None:
    parser = argparse.ArgumentParser(description="Build V3 art production report")
    parser.add_argument("--ids", help="comma-separated asset IDs")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in manifest["assets"]}
    wanted = set(x.strip() for x in args.ids.split(",")) if args.ids else set(assets)

    technical = {}
    technical_path = QA / "visual-qa.json"
    if technical_path.exists():
        technical = {x["asset_id"]: x for x in json.loads(technical_path.read_text(encoding="utf-8"))}

    rows = []
    for asset_id in sorted(wanted):
        if asset_id not in assets:
            continue
        vision_path = VISION / f"{asset_id}.json"
        vision = json.loads(vision_path.read_text(encoding="utf-8")) if vision_path.exists() else None
        rows.append({
            "id": asset_id,
            "key": assets[asset_id]["key"],
            "priority": assets[asset_id]["priority"],
            "technical_pass": technical.get(asset_id, {}).get("passed"),
            "vision_gate": vision.get("overall_gate") if vision else "NOT_REVIEWED",
            "recommended_action": vision.get("recommended_action") if vision else "HOLD_FOR_REFERENCE",
            "hard_failures": vision.get("hard_failures", []) if vision else [],
        })

    summary = {
        "schema_version": "1.0",
        "ai_review_is_not_final_approval": True,
        "total": len(rows),
        "pass_to_human": sum(x["vision_gate"] == "PASS_TO_HUMAN" for x in rows),
        "rework": sum(x["vision_gate"] == "REWORK" for x in rows),
        "hold": sum(x["vision_gate"] == "HOLD" for x in rows),
        "not_reviewed": sum(x["vision_gate"] == "NOT_REVIEWED" for x in rows),
        "rows": rows,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "v3-production-report.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out}")

if __name__ == "__main__":
    main()
