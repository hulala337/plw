from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "art-work" / "generated"
QA = ROOT / "art-work" / "qa"


def signature(path: Path):
    with Image.open(path).convert("RGB") as im:
        im.thumbnail((64, 64))
        stat = ImageStat.Stat(im)
        return {
            "mean": stat.mean,
            "rms": stat.rms,
            "size": Image.open(path).size,
        }


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a["mean"], b["mean"])))


def main() -> None:
    files = sorted(GENERATED.glob("*.*")) if GENERATED.exists() else []
    files = [p for p in files if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    sigs = {p.stem: signature(p) for p in files}

    pairs = []
    for i, left in enumerate(files):
        for right in files[i + 1:]:
            pairs.append({
                "left": left.stem,
                "right": right.stem,
                "mean_rgb_distance": round(distance(sigs[left.stem], sigs[right.stem]), 3),
            })

    report = {
        "method": "heuristic color/statistical comparison only",
        "warning": "This is not a semantic or art-director replacement. Human review remains mandatory.",
        "assets": sigs,
        "pairs": sorted(pairs, key=lambda x: x["mean_rgb_distance"]),
    }
    QA.mkdir(parents=True, exist_ok=True)
    out = QA / "consistency-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"checked {len(files)} images")
    print(f"report: {out}")


if __name__ == "__main__":
    main()
