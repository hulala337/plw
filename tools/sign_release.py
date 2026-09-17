from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PROTECTED = [
    "VERSION.txt",
    "web/index.html",
    "web/assets/app.js",
    "web/assets/style.css",
    "web/assets/wechat_qr.png",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_or_create_private(path: Path) -> Ed25519PrivateKey:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raw = path.read_bytes()
        if len(raw) != 32:
            raise SystemExit(f"invalid Ed25519 private key length: {path}")
        return Ed25519PrivateKey.from_private_bytes(raw)
    key = Ed25519PrivateKey.generate()
    path.write_bytes(key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    ))
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--private-key", required=True)
    args = p.parse_args()
    root = Path(args.root).resolve()
    security = root / "security"
    security.mkdir(exist_ok=True)
    key = load_or_create_private(Path(args.private_key).expanduser().resolve())

    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    public_b64 = base64.b64encode(public).decode("ascii")
    (security / "public_key.py").write_text(
        "# Generated at release-build time. Public key only; do not replace without the matching private key.\n"
        f'PINNED_PUBLIC_KEY_B64 = "{public_b64}"\n',
        encoding="utf-8",
    )

    entries = []
    for rel in PROTECTED:
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"missing protected file: {rel}")
        entries.append({"path": rel, "sha256": sha256(path)})

    manifest = {
        "format": 1,
        "product": "Pelican Workbench",
        "version": args.version,
        "publisher": "TF7Z-XY",
        "files": entries,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (security / "release_manifest.json").write_bytes(manifest_bytes)
    sig = key.sign(manifest_bytes)
    (security / "release_manifest.sig").write_text(base64.b64encode(sig).decode("ascii"), encoding="ascii")
    print("Signed protected assets:")
    for rel in PROTECTED:
        print("  -", rel)
    print("Private key:", Path(args.private_key).expanduser().resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
