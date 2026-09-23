from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "art-production-spec" / "ART_PRODUCTION_STATE.json"
MANIFEST_PATH = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
REQUIRED = [
    ROOT / "ART_HANDOFF.md",
    STATE_PATH,
    MANIFEST_PATH,
    ROOT / "art-production-spec" / "CHARACTER_BIBLE.md",
    ROOT / "art-production-spec" / "ART_DIRECTION.md",
    ROOT / "art-production-spec" / "PRODUCTION_RULES.md",
]

def fail(message: str, errors: list[str]) -> None:
    errors.append(message)

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Pelican Workbench art-production handoff state.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    for path in REQUIRED:
        if not path.exists():
            fail(f"MISSING: {path.relative_to(ROOT)}", errors)

    if errors:
        result = {"status": "FAIL", "errors": errors, "warnings": warnings}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else "\n".join(["HANDOFF CHECK: FAIL", *errors]))
        return 1

    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"INVALID JSON: {exc}")
        result = {"status": "FAIL", "errors": errors, "warnings": warnings}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"HANDOFF CHECK: FAIL\n{errors[-1]}")
        return 1

    assets = {item.get("id"): item for item in manifest.get("assets", [])}
    current = state.get("current_asset")
    current_key = state.get("current_key")

    if state.get("handoff_document") != "ART_HANDOFF.md":
        errors.append("HANDOFF DOCUMENT: state.handoff_document must be ART_HANDOFF.md.")

    if state.get("style_anchor") != "B01":
        errors.append("STYLE ANCHOR: current style_anchor must be B01.")

    if current not in assets:
        errors.append(f"CURRENT ASSET: {current!r} is not present in ART_ASSET_MANIFEST.json.")
    else:
        if assets[current].get("key") != current_key:
            errors.append(
                f"CURRENT KEY MISMATCH: state says {current_key!r}, "
                f"manifest says {assets[current].get('key')!r}."
            )
        if state.get("current_status") in {"APPROVED", "FROZEN"}:
            errors.append("CURRENT STATUS: handoff cannot resume from APPROVED/FROZEN without an explicit rework/version record.")

    expected = {
        "B01": "pelican_master",
        "B02": "pelican_working",
        "B03": "pelican_typing",
        "B04": "pelican_thinking",
        "B07": "pelican_drinking_coffee",
        "C01": "office_master",
        "C02": "office_day",
        "C03": "office_night",
        "E01": "dashboard_hero",
    }
    for asset_id, key in expected.items():
        actual = assets.get(asset_id, {}).get("key")
        if actual != key:
            errors.append(f"MANIFEST MISMATCH: {asset_id} must be {key!r}, found {actual!r}.")

    sequence = state.get("production_sequence", [])
    if sequence[:3] != ["B01", "B02", "B03"]:
        errors.append("SEQUENCE: first production anchors must be B01, B02, B03.")
    if current != "B04":
        warnings.append(f"Current asset is {current}; this is valid only if intentionally updated in the state file.")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "current_asset": current,
        "current_key": current_key,
        "current_status": state.get("current_status"),
        "next_action": state.get("next_action"),
        "style_anchor": state.get("style_anchor"),
        "production_sequence": sequence,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("========================================")
        print(" Pelican Workbench Art Handoff Check")
        print("========================================")
        print(f"Style Anchor : {result['style_anchor']}")
        print(f"Current      : {result['current_asset']} / {result['current_key']}")
        print(f"Status       : {result['current_status']}")
        print(f"Next Action  : {result['next_action']}")
        print(f"Sequence     : {' -> '.join(sequence)}")
        print(f"Result       : {result['status']}")
        if errors:
            print("\nErrors:")
            for item in errors:
                print(f" - {item}")
        if warnings:
            print("\nWarnings:")
            for item in warnings:
                print(f" - {item}")
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
