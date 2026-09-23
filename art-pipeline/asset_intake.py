from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_tree_to_zip(archive: zipfile.ZipFile, source_root: Path, included: list[str]) -> None:
    if not source_root.exists():
        return
    for path in sorted(source_root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(ROOT).as_posix()
            archive.write(path, rel)
            included.append(rel)


def build_return_package(output: Path, asset_id: str) -> Path:
    state = load_json(STATE_PATH)
    assets = manifest_assets()
    asset_id = resolve_asset_id(asset_id, state, assets)
    asset_dir = ASSET_ROOT / asset_id

    if not asset_dir.exists():
        raise IntakeError(f"资产目录不存在：{asset_dir.relative_to(ROOT)}")

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    included: list[str] = []
    metadata = {
        "schema_version": "1.0",
        "package_type": "RETURN",
        "project": state.get("project", "Pelican Workbench"),
        "repository": state.get("repository"),
        "asset_id": asset_id,
        "asset_key": assets[asset_id].get("key"),
        "source_current_status": state.get("current_status"),
        "source_next_action": state.get("next_action"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "human_review_required": True,
        "approval_is_not_automatic": True,
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("RETURN.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        archive.writestr(
            "RETURN.md",
            "\n".join([
                "# Pelican Workbench Return Package",
                "",
                f"- Asset: {asset_id} / {assets[asset_id].get('key')}",
                f"- Created: {metadata['created_at']}",
                "- 本包仅用于回传候选、审核和 QA 结果，不代表自动批准。",
                "- 接收方必须先校验本包，再导入 GitHub。",
                "",
            ]),
        )

        add_tree_to_zip(archive, asset_dir / "candidates", included)
        add_tree_to_zip(archive, asset_dir / "approved", included)
        add_tree_to_zip(archive, asset_dir / "qa", included)

        review = asset_dir / "review.json"
        if review.is_file():
            archive.write(review, review.relative_to(ROOT).as_posix())
            included.append(review.relative_to(ROOT).as_posix())

        for required in (STATE_PATH, MANIFEST_PATH, ROOT / "ART_HANDOFF.md", ROOT / "ART_SYNC_GUIDE.md"):
            if required.is_file():
                rel = required.relative_to(ROOT).as_posix()
                archive.write(required, rel)
                included.append(rel)

        checksums = {
            "schema_version": "1.0",
            "package_type": "RETURN",
            "asset_id": asset_id,
            "files": [
                {"path": rel, "sha256": sha256_file(ROOT / rel)}
                for rel in sorted(set(included))
                if (ROOT / rel).is_file()
            ],
        }
        archive.writestr("checksums.json", json.dumps(checksums, ensure_ascii=False, indent=2) + "\n")

    return output


def validate_return_package(package: Path) -> tuple[bool, list[str]]:
    package = package.expanduser().resolve()
    if not package.is_file():
        return False, [f"文件不存在：{package}"]

    errors: list[str] = []
    try:
        archive = zipfile.ZipFile(package, "r")
    except zipfile.BadZipFile as exc:
        return False, [f"不是有效 ZIP：{exc}"]

    with archive:
        names = set(archive.namelist())
        required = {"RETURN.json", "RETURN.md", "checksums.json"}
        missing = sorted(required - names)
        if missing:
            errors.append("缺少必要文件：" + ", ".join(missing))

        try:
            metadata = json.loads(archive.read("RETURN.json").decode("utf-8"))
        except Exception as exc:
            errors.append(f"RETURN.json 无法解析：{exc}")
            metadata = {}

        try:
            checksums = json.loads(archive.read("checksums.json").decode("utf-8"))
        except Exception as exc:
            errors.append(f"checksums.json 无法解析：{exc}")
            checksums = {}

        asset_id = str(metadata.get("asset_id", "")).upper()
        if not re.fullmatch(r"[A-Z]\d{2}", asset_id):
            errors.append(f"RETURN.json 的 asset_id 无效：{asset_id!r}")
        if metadata.get("package_type") != "RETURN":
            errors.append("package_type 必须为 RETURN。")
        if metadata.get("approval_is_not_automatic") is not True:
            errors.append("Return Package 必须声明不会自动批准。")

        entries = checksums.get("files", [])
        if not isinstance(entries, list):
            errors.append("checksums.json 的 files 必须是数组。")
            entries = []

        for entry in entries:
            rel = entry.get("path") if isinstance(entry, dict) else None
            expected = entry.get("sha256") if isinstance(entry, dict) else None
            if not isinstance(rel, str) or not isinstance(expected, str):
                errors.append("checksums.json 存在无效条目。")
                continue
            if rel not in names:
                errors.append(f"checksum 对应文件不在压缩包内：{rel}")
                continue
            actual = hashlib.sha256(archive.read(rel)).hexdigest()
            if actual != expected:
                errors.append(f"SHA-256 不匹配：{rel}")

        if asset_id:
            candidates = [
                name for name in names
                if f"art-assets/{asset_id}/candidates/" in name
                and not name.endswith("/")
                and Path(name).suffix.lower() in ALLOWED_EXTENSIONS
            ]
            if not candidates:
                errors.append(f"未找到 {asset_id} 的候选资产文件。")
            for name in candidates:
                if not VERSION_RE.match(Path(name).name):
                    errors.append(f"候选文件名不符合 <ASSET_ID>_vNN.ext：{name}")

        state_name = "art-production-spec/ART_PRODUCTION_STATE.json"
        if state_name in names:
            try:
                packaged_state = json.loads(
                    archive.read(state_name).decode("utf-8")
                )
                if str(packaged_state.get("current_asset", "")).upper() != asset_id:
                    errors.append("Return Package 的 asset_id 与打包时 STATE.current_asset 不一致。")
            except Exception as exc:
                errors.append(f"打包的 STATE 无法解析：{exc}")

    return not errors, errors


def run_import(args: argparse.Namespace) -> int:
    state = load_json(STATE_PATH)
    assets = manifest_assets()
    source = validate_source(Path(args.source))
    asset_id = resolve_asset_id(args.asset_id, state, assets)

    candidate_dir = ASSET_ROOT / asset_id / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    version = next_version(candidate_dir, asset_id)
    destination = candidate_dir / f"{asset_id}_v{version:02d}{source.suffix.lower()}"

    if destination.exists() and not args.force:
        raise IntakeError(f"目标文件已存在：{destination.relative_to(ROOT)}；为防止覆盖，已拒绝导入。")
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import Pelican Workbench art assets and create/validate Return Packages."
    )
    parser.add_argument("source", nargs="?", help="外部平台生成并下载到本机的图片/美术文件路径。")
    parser.add_argument("--asset-id", help="目标资产 ID，例如 B04。省略时使用 STATE.current_asset。")
    parser.add_argument("--copy", action="store_true", help="显式声明复制源文件（默认就是复制）。")
    parser.add_argument("--dry-run", action="store_true", help="只检查并显示目标路径，不实际复制。")
    parser.add_argument("--force", action="store_true", help="恢复误删的目标文件时允许覆盖同名目标。")
    parser.add_argument("--export-return-package", metavar="ZIP", help="导出当前资产 Return Package ZIP。")
    parser.add_argument("--validate-return-package", metavar="ZIP", help="校验 Return Package 的结构与 SHA-256。")
    args = parser.parse_args()

    try:
        if args.export_return_package:
            if args.source:
                raise IntakeError("--export-return-package 不能同时提供 source。")
            state = load_json(STATE_PATH)
            assets = manifest_assets()
            asset_id = resolve_asset_id(args.asset_id, state, assets)
            output = build_return_package(Path(args.export_return_package), asset_id)
            print("RETURN PACKAGE: EXPORTED")
            print(f"Asset ID : {asset_id}")
            print(f"Package  : {output}")
            return 0

        if args.validate_return_package:
            if args.source:
                raise IntakeError("--validate-return-package 不能同时提供 source。")
            ok, errors = validate_return_package(Path(args.validate_return_package))
            if ok:
                print("RETURN PACKAGE: PASS")
                return 0
            print("RETURN PACKAGE: FAIL", file=sys.stderr)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2

        if not args.source:
            parser.error("请提供 source，或使用 --export-return-package / --validate-return-package。")
        return run_import(args)

    except IntakeError as exc:
        print(f"ASSET INTAKE: FAIL\nERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ASSET INTAKE: FAIL\nFILE ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
