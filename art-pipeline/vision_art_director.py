from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
BIBLE = ROOT / "art-production-spec" / "CHARACTER_BIBLE.md"
DIRECTION = ROOT / "art-production-spec" / "ART_DIRECTION.md"
GENERATED = ROOT / "art-work" / "generated"
QA = ROOT / "art-work" / "qa" / "vision-review"

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "asset_id": {"type": "string"},
        "overall_gate": {"type": "string", "enum": ["PASS_TO_HUMAN", "REWORK", "HOLD"]},
        "recommended_action": {"type": "string", "enum": ["HUMAN_REVIEW", "REGENERATE", "MINOR_EDIT", "HOLD_FOR_REFERENCE"]},
        "technical_qa": {"type": "object", "additionalProperties": False, "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["score", "issues"]},
        "brief_compliance": {"type": "object", "additionalProperties": False, "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["score", "issues"]},
        "character_identity": {"type": "object", "additionalProperties": False, "properties": {
            "applicable": {"type": "boolean"},
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["applicable", "score", "issues"]},
        "style_consistency": {"type": "object", "additionalProperties": False, "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["score", "issues"]},
        "composition": {"type": "object", "additionalProperties": False, "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["score", "issues"]},
        "artifact_detection": {"type": "object", "additionalProperties": False, "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["score", "issues"]},
        "originality_guard": {"type": "object", "additionalProperties": False, "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "string"}}
        }, "required": ["score", "issues"]},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "hard_failures": {"type": "array", "items": {"type": "string"}}
    },
    "required": [
        "asset_id", "overall_gate", "recommended_action", "technical_qa",
        "brief_compliance", "character_identity", "style_consistency",
        "composition", "artifact_detection", "originality_guard",
        "reasons", "hard_failures"
    ]
}

def read_ids(value: str | None):
    return [x.strip() for x in value.split(",") if x.strip()] if value else None

def image_data_url(path: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[path.suffix.lower()]
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"

def review_one(client: OpenAI, asset: dict, image_path: Path, reference_paths: list[Path], model: str) -> dict:
    bible = BIBLE.read_text(encoding="utf-8")
    direction = DIRECTION.read_text(encoding="utf-8")
    refs = "\n".join(f"- {p.name}" for p in reference_paths) or "- none"

    prompt = f"""You are the V3 AI Vision Art Director for Pelican Workbench.
Review the supplied candidate image as a production gate, not as a generic image critic.

Asset:
{json.dumps(asset, ensure_ascii=False, indent=2)}

Reference files available to the pipeline:
{refs}

Character Bible:
{bible}

Art Direction:
{direction}

Review rules:
1. Compare the candidate against the asset brief, Character Bible and Art Direction.
2. For character assets, inspect bill shape/color, eye spacing, head/body ratio, feather silhouette, wing anatomy and identity continuity.
3. For office/scenes, inspect recurring window, desk, plant, lamp, cup, city/water logic, light direction and spatial continuity.
4. Detect malformed anatomy, duplicate objects, impossible joins, accidental text/gibberish, broken transparency/composition, plastic 3D or photorealism.
5. Treat originality as a guard: flag obvious copying of a distinctive third-party character/logo/scene. Do not attempt legal conclusions.
6. Do not reward a candidate merely because it is attractive. It must fit this product's visual system.
7. Never approve automatically. overall_gate PASS_TO_HUMAN means it is good enough to enter human review, not final approval.
8. Any Character Bible hard rejection condition must force overall_gate=REWORK.
9. Be conservative: when evidence is unclear, use HOLD rather than guessing.
10. Return only the required structured JSON.
"""

    content = [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": image_data_url(image_path)},
    ]
    for ref in reference_paths[:3]:
        content.append({"type": "input_image", "image_url": image_data_url(ref)})

    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_schema", "name": "pelican_art_review", "strict": True, "schema": SCHEMA}},
    )
    return json.loads(response.output_text)

def main() -> None:
    parser = argparse.ArgumentParser(description="V3 AI Vision Art Director")
    parser.add_argument("--ids", help="comma-separated asset IDs")
    parser.add_argument("--model", default=os.getenv("OPENAI_REVIEW_MODEL", "gpt-5.6-luna"))
    args = parser.parse_args()

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in manifest["assets"]}
    wanted = set(read_ids(args.ids) or assets.keys())
    QA.mkdir(parents=True, exist_ok=True)

    pelican_refs = sorted((ROOT / "art-work" / "references" / "pelican").glob("*.*")) if (ROOT / "art-work" / "references" / "pelican").exists() else []
    office_refs = sorted((ROOT / "art-work" / "references" / "office").glob("*.*")) if (ROOT / "art-work" / "references" / "office").exists() else []
    pelican_refs = [p for p in pelican_refs if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    office_refs = [p for p in office_refs if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]

    for asset_id in sorted(wanted):
        asset = assets.get(asset_id)
        image = GENERATED / f"{asset_id}.png"
        if not asset or not image.exists():
            print(f"SKIP {asset_id}: candidate missing")
            continue
        try:
            category = asset.get("category", "")
            refs = pelican_refs if category == "character" or asset_id.startswith("B") else office_refs if category in {"environment", "weather"} or asset_id.startswith("C") else []
            result = review_one(client, asset, image, refs, args.model)
            out = QA / f"{asset_id}.json"
            out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{result['overall_gate']}: {asset_id} -> {out}")
        except Exception as exc:
            print(f"ERROR {asset_id}: {exc}")

if __name__ == "__main__":
    main()
