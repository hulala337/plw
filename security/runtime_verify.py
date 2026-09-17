from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from .public_key import PINNED_PUBLIC_KEY_B64
except Exception:
    Ed25519PublicKey = None
    PINNED_PUBLIC_KEY_B64 = ""

MANIFEST_NAME = "release_manifest.json"
SIGNATURE_NAME = "release_manifest.sig"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_release_integrity(base: Path) -> tuple[bool, str]:
    """Verify signed protected resources in a compiled release.

    The public verification key is pinned in compiled Python code. The private
    key never ships with the product and is kept on the publisher's build host.
    """
    sec = base / "security"
    manifest_path = sec / MANIFEST_NAME
    sig_path = sec / SIGNATURE_NAME
    if not (manifest_path.exists() and sig_path.exists()):
        return False, "完整性校验文件缺失"
    if not PINNED_PUBLIC_KEY_B64:
        return False, "发布公钥未内置"

    try:
        manifest_bytes = manifest_path.read_bytes()
        signature = base64.b64decode(sig_path.read_text(encoding="ascii").strip())
        public_bytes = base64.b64decode(PINNED_PUBLIC_KEY_B64.strip())
        if Ed25519PublicKey is None or len(public_bytes) != 32:
            return False, "缺少或无效的 Ed25519 验签模块"
        Ed25519PublicKey.from_public_bytes(public_bytes).verify(signature, manifest_bytes)
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except Exception as exc:
        return False, f"签名校验失败：{exc}"

    expected_version = str(manifest.get("version", "")).strip()
    if not expected_version:
        return False, "发布清单版本无效"

    for item in manifest.get("files", []):
        rel = Path(str(item.get("path", "")))
        expected = str(item.get("sha256", "")).lower()
        if not rel or rel.is_absolute() or ".." in rel.parts:
            return False, "发布清单包含非法路径"
        target = (base / rel).resolve()
        try:
            target.relative_to(base.resolve())
        except ValueError:
            return False, "发布清单路径越界"
        if not target.exists() or not target.is_file():
            return False, f"受保护文件缺失：{rel.as_posix()}"
        if _sha256(target).lower() != expected:
            return False, f"文件已修改：{rel.as_posix()}"

    return True, "ok"
