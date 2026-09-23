from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "art-production-spec" / "ART_PRODUCTION_STATE.json"
MANIFEST_PATH = ROOT / "art-production-spec" / "ART_ASSET_MANIFEST.json"
ASSET_ROOT = ROOT / "art-assets"

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".psd", ".svg"}
VERSION_RE = re.compile(r"^(?P<asset>[A-Z]\d{2})_v(?P<version>\d{2,})\.(?P<ext>[A-Za-z0-9]+)$")


class IntakeError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IntakeError(f"无法读取 JSON：{path.relative_to(ROOT)}：{exc}") from exc


def manifest_assets() -> dict[str, dict]:
    data = load_json(MANIFEST_PATH)
    return {item["id"]: item for item in data.get("assets", []) if item.get("id")}


def next_version(candidate_dir: Path, asset_id: str) -> int:
    maximum = 0
    if candidate_dir.exists():
        for path in candidate_dir.iterdir():
            if not path.is_file():
                continue
            match = VERSION_RE.match(path.name)
            if match and match.group("asset") == asset_id:
                maximum = max(maximum, int(match.group("version")))
    return maximum + 1


def resolve_asset_id(requested: str | None, state: dict, assets: dict[str, dict]) -> str:
    asset_id = requested or state.get("current_asset")
    if not asset_id:
        raise IntakeError("STATE 没有 current_asset；请使用 --asset-id 明确指定资产。")
    asset_id = asset_id.upper()
    if asset_id not in assets:
        raise IntakeError(f"资产 ID {asset_id!r} 不存在于 ART_ASSET_MANIFEST.json。")
    return asset_id


def validate_source(source: Path) -> Path:
    source = source.expanduser().resolve()
    if not source.exists():
        raise IntakeError(f"源文件不存在：{source}")
    if not source.is_file():
        raise IntakeError(f"源路径不是文件：{source}")
    if source.suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise IntakeError(f"不支持的扩展名 {source.suffix!r}；允许：{allowed}")
    return source


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import an externally generated Pelican Workbench art asset as a unique candidate."
    )
    parser.add_argument("source", help="外部平台生成并下载到本机的图片/美术文件路径。")
    parser.add_argument(
        "--asset-id",
        help="目标资产 ID，例如 B04。省略时使用 STATE.current_asset。",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="保留源文件并复制到候选目录；默认行为也是复制，保留此参数仅为兼容显式调用。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只检查并显示目标路径，不实际复制。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="仅用于恢复误删的目标文件；默认禁止覆盖同名文件。",
    )
    args = parser.parse_args()

    try:
        state = load_json(STATE_PATH)
        assets = manifest_assets()
        source = validate_source(Path(args.source))
        asset_id = resolve_asset_id(args.asset_id, state, assets)

        candidate_dir = ASSET_ROOT / asset_id / "candidates"
        candidate_dir.mkdir(parents=True, exist_ok=True)

        version = next_version(candidate_dir, asset_id)
        destination = candidate_dir / f"{asset_id}_v{version:02d}{source.suffix.lower()}"

        if destination.exists() and not args.force:
            raise IntakeError(
                f"目标文件已存在：{destination.relative_to(ROOT)}；"
                "为防止覆盖，已拒绝导入。"
            )

        if source == destination.resolve():
            raise IntakeError("源文件已经位于目标位置，无需再次导入。")

        if args.dry_run:
            print("ASSET INTAKE: DRY RUN")
        else:
            if destination.exists() and args.force:
                destination.unlink()
            shutil.copy2(source, destination)
            print("ASSET INTAKE: IMPORTED")

        print(f"Asset ID   : {asset_id}")
        print(f"Asset Key  : {assets[asset_id].get('key')}")
        print(f"Source     : {source}")
        print(f"Candidate  : {destination.relative_to(ROOT)}")
        print("Status     : GENERATED / HUMAN REVIEW REQUIRED")
        print("Next       : run QA, inspect the actual image, then persist the candidate to Git.")

        return 0

    except IntakeError as exc:
        print(f"ASSET INTAKE: FAIL\nERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ASSET INTAKE: FAIL\nFILE ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
