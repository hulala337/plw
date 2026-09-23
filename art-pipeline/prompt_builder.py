from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
OUT = ROOT / "art-work" / "prompts"

GLOBAL_STYLE = """
Pelican Workbench original illustration system.
Warm, smart, relaxed, companion-like productivity.
Cute but not childish; premium editorial illustration; cozy productivity;
soft pastel palette; subtle depth; hand-crafted digital illustration feel.
Consistent Pelican character design: white/light-gray feathers, soft blue-gray
shadows, bright yellow-orange bill, rounded head and body, simple expressive
eyes, stable proportions and visual weight.
Clean desktop software art direction, clear focal hierarchy, nuanced soft
lighting, restrained texture, polished professional finish.
Do not imitate or reproduce any third-party character, logo, trademark,
composition, or distinctive scene.
No rendered text, labels, UI text, watermark, signature, gibberish, extra
limbs, duplicated objects, malformed hands/wings, distorted face, plastic
3D, photorealism, generic mascot styling, or geometric-SVG look.
"""

CATEGORY_NOTES = {
    "character": "Keep the Pelican identity locked. Show the requested pose/state clearly and preserve face, bill, eyes, body proportions and feather silhouette.",
    "environment": "Use a coherent recurring office architecture. Window, desk, plant, lamp, monitor and cup belong to one visual world.",
    "dashboard": "Compose for a desktop productivity dashboard: strong focal subject, readable negative space, polished hero illustration.",
    "state": "Communicate the work state through body language and a small number of contextual props; avoid literal UI text.",
    "timeline": "Simple, legible pictorial symbol suitable for a compact timeline; preserve the same illustration language.",
    "analytics": "Use restrained visual storytelling that supports data-oriented software without becoming a cartoon sticker.",
    "achievement": "Badge-like celebratory illustration with clear silhouette and reusable small-size readability.",
    "onboarding": "Friendly explanatory illustration; privacy and permissions should feel reassuring rather than alarming.",
    "settings": "Clean supporting illustration for a desktop settings surface.",
    "empty_state": "Gentle, optimistic illustration that communicates absence of data without implying an error.",
    "error": "Calm diagnostic illustration; never depict danger or panic unless the brief explicitly requires it.",
    "weather": "Atmospheric layer consistent with the office world; avoid changing the core character or architecture.",
    "decor": "Small reusable decorative element with restrained detail and transparent-background suitability.",
    "marketing": "Polished brand illustration suitable for promotional material while remaining consistent with the product UI.",
    "tray": "Compact, instantly recognizable desktop-tray visual language.",
    "brand": "Brand asset with exceptionally clean silhouette and no accidental generated lettering.",
}


def load_assets():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]


def build(asset: dict) -> str:
    note = CATEGORY_NOTES.get(asset["category"], "")
    return f"""Create one original Pelican Workbench production asset.

Asset ID: {asset["id"]}
Asset key: {asset["key"]}
Category: {asset["category"]}
Priority: {asset["priority"]}
Type: {asset["type"]}

{GLOBAL_STYLE}

Specific production requirement:
{note}

Asset-specific brief:
- The asset must visually communicate "{asset["key"]}".
- Preserve a coherent relationship with the rest of the Pelican Workbench art system.
- Prefer a clean focal subject and intentional composition over excessive detail.
- If the asset is a character, preserve the master Pelican identity.
- If the asset is a scene, keep the office architecture coherent across time/weather variants.
- If transparency is appropriate, isolate the subject cleanly with a transparent background.
- Do not put any words, letters, numbers, logos, UI labels, watermark or signature into the image.

This is a production candidate, not a sketch. Render at high quality with polished edges,
controlled lighting, consistent materials, subtle depth, and a finished editorial-illustration feel.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="comma-separated asset IDs; default: all PLANNED assets")
    args = parser.parse_args()

    assets = load_assets()
    wanted = {x.strip() for x in args.ids.split(",")} if args.ids else None
    OUT.mkdir(parents=True, exist_ok=True)

    count = 0
    for asset in assets:
        if wanted and asset["id"] not in wanted:
            continue
        if not wanted and asset["status"] != "PLANNED":
            continue
        path = OUT / f'{asset["id"]}_{asset["key"]}.txt'
        path.write_text(build(asset), encoding="utf-8")
        count += 1

    print(f"prompts written: {count}")
    print(f"directory: {OUT}")


if __name__ == "__main__":
    main()
