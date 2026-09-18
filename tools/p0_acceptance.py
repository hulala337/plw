from __future__ import annotations

"""Deterministic P0 contract checker.

Run from the repository root:
    python tools/p0_acceptance.py

This checker does not fake keyboard or mouse input. Real Windows behavior
remains a runtime acceptance gate documented in docs/P0_ACCEPTANCE_MATRIX.md.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
HTML = ROOT / "web" / "index.html"
JS = ROOT / "web" / "assets" / "app.js"

REQUIRED_ROUTES = {
    "/", "/api/health", "/api/dashboard", "/api/display-info",
    "/api/settings", "/api/todos", "/api/todos/{todo_id}",
    "/api/forget-today", "/api/replay", "/api/export/csv",
    "/api/export/xlsx", "/api/growth",
}
REQUIRED_VIEWS = {"home", "replay", "timeline", "stats", "growth", "settings"}

def main() -> int:
    app = APP.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    routes = set(re.findall(r'@api\.(?:get|post|patch|delete)\("([^"]+)"', app))
    missing = REQUIRED_ROUTES - routes
    if missing:
        raise RuntimeError("missing API routes: " + ", ".join(sorted(missing)))

    html_ids = set(re.findall(r'id="([^"]+)"', html))
    js_ids = set(re.findall(r"\$\('([^']+)'\)", js))
    missing_ids = sorted(js_ids - html_ids)
    if missing_ids:
        raise RuntimeError("frontend DOM IDs missing: " + ", ".join(missing_ids))

    nav_views = set(re.findall(r'class="nav[^"]*"[^>]*data-view="([^"]+)"', html))
    if REQUIRED_VIEWS - nav_views:
        raise RuntimeError("main navigation missing: " + ", ".join(sorted(REQUIRED_VIEWS - nav_views)))
    for view in REQUIRED_VIEWS:
        if f'id="view-{view}"' not in html:
            raise RuntimeError("view section missing: " + view)

    for token in (
        "persist_tracker_tick", "queue_input", "cursor_distance_px",
        "monitor_switches", "CREATE TABLE IF NOT EXISTS daily",
        "CREATE TABLE IF NOT EXISTS focus_sessions",
    ):
        if token not in app:
            raise RuntimeError("backend token missing: " + token)

    for token in (
        "data-view-jump", "/api/todos", "/api/replay", "/api/settings",
        "/api/export/csv", "/api/export/xlsx", "setView(",
    ):
        if token not in js:
            raise RuntimeError("frontend token missing: " + token)

    print("Pelican Workbench P0 contract: PASS")
    print("Runtime gates still required: Windows input, SQLite persistence, monitor crossing, UI click-through.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Pelican Workbench P0 contract: FAIL:", exc)
        raise SystemExit(1)
