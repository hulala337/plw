from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data" / "history_asset_registry_v3_2.json"
TIMEOUT = 45
USER_AGENT = "RuowoshiTamenV32/3.2.1 historical-asset-bootstrap"


def download_one(item: dict) -> Path:
    target = ROOT / item["local_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        item["download_url"],
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        content_type = (response.headers.get("Content-Type") or "").lower()
        data = response.read()
    if "image/" not in content_type:
        raise RuntimeError(
            f"{item['id']}: remote content is not an image: {content_type or 'unknown'}"
        )
    minimum = int(item.get("min_bytes", 1))
    if len(data) < minimum:
        raise RuntimeError(
            f"{item['id']}: downloaded file is too small: {len(data)} < {minimum} bytes"
        )
    target.write_bytes(data)
    return target


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assets = registry.get("assets", [])
    if not assets:
        raise RuntimeError("history asset registry is empty")
    print(f"[history-assets] bootstrapping {len(assets)} historical images...")
    for item in assets:
        path = ROOT / item["local_path"]
        if path.is_file() and path.stat().st_size >= int(item.get("min_bytes", 1)):
            print(f"[history-assets] EXISTS  {item['id']} -> {path.relative_to(ROOT)}")
            continue
        try:
            saved = download_one(item)
        except Exception as exc:
            print(f"[history-assets] FAILED  {item['id']}: {exc}", file=sys.stderr)
            return 2
        print(
            f"[history-assets] DOWNLOADED {item['id']} -> "
            f"{saved.relative_to(ROOT)} ({saved.stat().st_size} bytes)"
        )
    print("[history-assets] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
