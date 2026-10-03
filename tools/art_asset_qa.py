"""Build and validate the deterministic art asset catalog."""
from pathlib import Path
import hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "web" / "assets" / "illustrations"
OUT = ROOT / "art-assets" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
rows=[]; errors=[]
for path in sorted(ASSET_ROOT.glob("*.svg")):
    text=path.read_text(encoding="utf-8")
    viewbox=re.search(r"viewBox=[\"']([^\"']+)", text, re.I)
    if not viewbox: errors.append(f"missing viewBox: {path.name}")
    if "<script" in text.lower(): errors.append(f"script tag: {path.name}")
    rows.append({"id": path.stem, "path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "viewBox": viewbox.group(1) if viewbox else None, "bytes": path.stat().st_size})
manifest={"schema":1,"style":"pelican-v36","source":"web/assets/illustrations","assets":rows,"errors":errors}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"assets":len(rows),"errors":errors,"manifest":str((OUT/"manifest.json").relative_to(ROOT))},ensure_ascii=False))
if errors: raise SystemExit(1)
