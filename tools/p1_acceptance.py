from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app.py"; HTML=ROOT/"web"/"index.html"; JS=ROOT/"web"/"assets"/"app.js"

REQUIRED_ROUTES={"/api/growth","/api/equipment"}
REQUIRED_TABLES={"progress_profile","progress_events","unlocks","achievements","equipment","scenes","pelicans","outfits","accessories","decorations","effects"}
REQUIRED_COLLECTION_IDS={"growthScenes","growthPelicans","growthOutfits","growthAccessories","growthDecorations","growthEffects"}

def main():
    app=APP.read_text(encoding="utf-8"); html=HTML.read_text(encoding="utf-8"); js=JS.read_text(encoding="utf-8")
    routes=set(re.findall(r'@api\.(?:get|post|patch|delete)\("([^"]+)"',app))
    if REQUIRED_ROUTES-routes: raise RuntimeError("missing P1 routes: "+", ".join(sorted(REQUIRED_ROUTES-routes)))
    tables=set(re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)',app))
    if REQUIRED_TABLES-tables: raise RuntimeError("missing P1 tables: "+", ".join(sorted(REQUIRED_TABLES-tables)))
    ids=set(re.findall(r'id="([^"]+)"',html))
    if REQUIRED_COLLECTION_IDS-ids: raise RuntimeError("missing Growth collection DOM: "+", ".join(sorted(REQUIRED_COLLECTION_IDS-ids)))
    for token in ("UNLOCK_CATALOG","ACHIEVEMENT_CATALOG","progress_events","growth_payload","world_payload","patch_equipment","total_active_seconds"):
        if token not in app: raise RuntimeError("missing P1 backend contract: "+token)
    for token in ("growthScenes","growthPelicans","growthOutfits","growthAccessories","growthDecorations","growthEffects","/api/equipment"):
        if token not in js: raise RuntimeError("missing P1 frontend contract: "+token)
    print("Pelican Workbench P1 contract: PASS")
    print("Runtime gates still required: Windows input, real SQLite persistence, monitor topology, UI interaction and packaged EXE.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
