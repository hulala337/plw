"""Release preflight checks that do not require a Windows desktop."""
from pathlib import Path
import ast, hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
required = [ROOT / "app.py", ROOT / "requirements.lock", ROOT / "VERSION.txt", ROOT / "web/index.html", ROOT / "web/assets/app.js"]
missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
if missing:
    print(json.dumps({"ok": False, "missing": missing}, ensure_ascii=False)); raise SystemExit(1)
ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
assets = {}
for p in sorted((ROOT / "web").rglob("*")):
    if p.is_file():
        assets[str(p.relative_to(ROOT)).replace("\\", "/")] = hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT / "build").mkdir(exist_ok=True)
(ROOT / "build" / "asset-manifest.json").write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"ok": True, "assets": len(assets), "python": sys.version.split()[0]}, ensure_ascii=False))
