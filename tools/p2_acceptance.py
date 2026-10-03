"""Deterministic P2 gate for data-driven world and progression contracts."""
from pathlib import Path
import re, sys
root = Path(__file__).resolve().parents[1]
app = (root / "app.py").read_text(encoding="utf-8")
web = (root / "web/index.html").read_text(encoding="utf-8")
required = ["world_payload", "growth_payload", "patch_equipment", "sync_progression", "forget_today"]
missing = [name for name in required if f"def {name}" not in app]
for marker in ('id="view-growth"', 'id="view-replay"', 'id="view-timeline"', 'id="view-stats"'):
    if marker not in web: missing.append(marker)
if missing:
    print("P2 contract: FAIL", ", ".join(missing)); raise SystemExit(1)
print("Pelican Workbench P2 contract: PASS")
print("Runtime gates still required: art review, animation, fresh install, multi-monitor topology.")
