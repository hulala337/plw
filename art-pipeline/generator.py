from __future__ import annotations

import argparse
import base64
import json
import os
import time
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "art-work" / "prompts"
OUT = ROOT / "art-work" / "generated"


def read_ids(value: str | None):
    return [x.strip() for x in value.split(",") if x.strip()] if value else None


def save_response(item, target: Path) -> None:
    if getattr(item, "b64_json", None):
        target.write_bytes(base64.b64decode(item.b64_json))
        return
    if getattr(item, "url", None):
        import urllib.request
        with urllib.request.urlopen(item.url, timeout=120) as r:
            target.write_bytes(r.read())
        return
    raise RuntimeError("Image API returned neither b64_json nor url")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="comma-separated asset IDs")
    parser.add_argument("--size", default="1536x1024")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--background", default="auto")
    parser.add_argument("--model", default=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )

    wanted = read_ids(args.ids)
    prompts = sorted(PROMPTS.glob("*.txt"))
    if wanted:
        prompts = [p for p in prompts if p.name.split("_", 1)[0] in wanted]

    OUT.mkdir(parents=True, exist_ok=True)

    for prompt_file in prompts:
        asset_id = prompt_file.name.split("_", 1)[0]
        prompt = prompt_file.read_text(encoding="utf-8")
        target = OUT / f"{asset_id}.png"

        if target.exists():
            print(f"SKIP {asset_id}: {target.name} already exists")
            continue

        last_error = None
        for attempt in range(1, args.retries + 2):
            try:
                print(f"GENERATE {asset_id} attempt={attempt}")
                result = client.images.generate(
                    model=args.model,
                    prompt=prompt,
                    size=args.size,
                    quality=args.quality,
                    background=args.background,
                )
                save_response(result.data[0], target)
                print(f"OK {asset_id}: {target}")
                break
            except Exception as exc:
                last_error = exc
                print(f"FAIL {asset_id}: {exc}")
                if attempt <= args.retries:
                    time.sleep(2 * attempt)
        else:
            print(f"ERROR {asset_id}: {last_error}")

    print(f"generated directory: {OUT}")


if __name__ == "__main__":
    main()
