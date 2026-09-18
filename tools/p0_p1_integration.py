from __future__ import annotations

"""Cross-layer P0/P1 contract checker.

This verifies that the reliable tracking foundation (P0) is actually wired
into progression/world (P1). It is intentionally deterministic and does not
pretend to perform Windows runtime acceptance.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
HTML = ROOT / "web" / "index.html"
JS = ROOT / "web" / "assets" / "app.js"

P0_ROUTES = {
    "/", "/api/health", "/api/dashboard", "/api/display-info",
    "/api/settings", "/api/todos", "/api/todos/{todo_id}",
    "/api/forget-today", "/api/replay", "/api/export/csv",
    "/api/export/xlsx",
}
P1_ROUTES = {"/api/growth", "/api/equipment"}
VIEWS = {"home", "replay", "timeline", "stats", "growth", "settings"}
P1_TABLES = {
    "progress_profile", "progress_events", "unlocks", "achievements",
    "equipment", "scenes", "pelicans", "outfits", "accessories",
    "decorations", "effects",
}
COLLECTION_IDS = {
    "growthScenes", "growthPelicans", "growthOutfits",
    "growthAccessories", "growthDecorations", "growthEffects",
}

def main() -> int:
    app = APP.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    routes = set(re.findall(r'@api\.(?:get|post|patch|delete)\("([^"]+)"', app))
    missing = (P0_ROUTES | P1_ROUTES) - routes
    if missing:
        raise RuntimeError("missing P0/P1 routes: " + ", ".join(sorted(missing)))

    tables = set(re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', app))
    if P1_TABLES - tables:
        raise RuntimeError("missing P1 tables: " + ", ".join(sorted(P1_TABLES - tables)))

    html_ids = set(re.findall(r'id="([^"]+)"', html))
    js_ids = set(re.findall(r"\$\('([^']+)'\)", js))
    missing_ids = sorted(js_ids - html_ids)
    if missing_ids:
        raise RuntimeError("frontend DOM IDs missing: " + ", ".join(missing_ids))

    nav_views = set(re.findall(r'class="nav[^"]*"[^>]*data-view="([^"]+)"', html))
    if VIEWS - nav_views:
        raise RuntimeError("main navigation missing: " + ", ".join(sorted(VIEWS - nav_views)))
    for view in VIEWS:
        if f'id="view-{view}"' not in html:
            raise RuntimeError("view section missing: " + view)

    # P0 -> P1 data path: input/tracker persistence must feed progression,
    # and the normalized World projection must consume the P1 equipment state
    # plus P0 display/work-state signals.
    required_app_tokens = (
        "queue_input", "persist_tracker_tick", "cursor_distance_px",
        "monitor_switches", "total_active_seconds",
        "sync_progression", "growth_payload", "world_payload",
        "display_info()", "active_session()",
        '"/api/equipment"', "UNLOCK_CATALOG", "ACHIEVEMENT_CATALOG",
    )
    for token in required_app_tokens:
        if token not in app:
            raise RuntimeError("cross-layer backend token missing: " + token)

    required_js_tokens = (
        "state.data?.world", "world.display_count", "world.scene",
        "world.pelican", "/api/growth", "/api/equipment",
    )
    for token in required_js_tokens:
        if token not in js:
            raise RuntimeError("cross-layer frontend token missing: " + token)

    # Guard the critical anti-regression rules explicitly.
    if 'last_input_ts = 0.0' not in app:
        raise RuntimeError("startup input timestamp guard missing")
    if 'total_active_seconds=total_active_seconds+?' not in app:
        raise RuntimeError("active-time -> lifetime progression persistence missing")
    if '"current_monitor_index": current_index' not in app:
        raise RuntimeError("current monitor is not exposed to the P0/P1 world boundary")
    if '"status": "ok" if listeners_healthy() and' not in app:
        raise RuntimeError("health status does not include tracker/database")

    # Both acceptance checkers must remain present so the integration gate
    # complements, rather than replaces, the individual P0/P1 contracts.
    if not (ROOT / "tools" / "p0_acceptance.py").is_file():
        raise RuntimeError("P0 acceptance checker missing")
    if not (ROOT / "tools" / "p1_acceptance.py").is_file():
        raise RuntimeError("P1 acceptance checker missing")

    print("Pelican Workbench P0/P1 integration contract: PASS")
    print("Runtime gates still required: real Windows input, SQLite restart persistence, monitor topology, UI click-through, packaged EXE.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
