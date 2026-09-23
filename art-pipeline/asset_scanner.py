from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
WORK = ROOT / "art-work"
REPORTS = WORK / "reports"


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = data["assets"]

    REPORTS.mkdir(parents=True, exist_ok=True)
    for name in ["prompts", "generated", "candidates", "approved", "rejected", "qa", "reviews"]:
        (WORK / name).mkdir(parents=True, exist_ok=True)

    by_priority = Counter(a["priority"] for a in assets)
    by_category = Counter(a["category"] for a in assets)
    report = {
        "schema_version": data.get("schema_version"),
        "total_assets": len(assets),
        "by_priority": dict(sorted(by_priority.items())),
        "by_category": dict(sorted(by_category.items())),
        "status_counts": dict(Counter(a["status"] for a in assets)),
        "next_recommended_batch": [
            a["id"] for a in assets
            if a["id"] in {"B01", "B02", "B03", "B04", "B07", "B11", "C01", "C02", "C03", "E01"}
        ],
    }
    out = REPORTS / "asset-inventory.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"assets: {len(assets)}")
    print("priority:", dict(by_priority))
    print("categories:", dict(by_category))
    print(f"report: {out}")


if __name__ == "__main__":
    main()
