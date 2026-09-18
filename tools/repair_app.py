from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def replace_if_present(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def repair(text: str) -> str:
    required = ('monitor_layout_signature','math.isfinite(dist) and dist >= 0','def self_test() -> int:','WHERE date(slice_start) BETWEEN ? AND ?','recover_stale_sessions()')
    if all(marker in text for marker in required):
        return text

    text = replace_if_present(
        text,
        '''def monitor_at(x: int, y: int) -> int | None:\n    for m in refresh_monitor_layout():\n        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:\n            return int(m["index"])\n    return None\n''',
        '''def monitor_at(x: int, y: int) -> int | None:\n    layout = refresh_monitor_layout()\n    for m in layout:\n        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:\n            return int(m["index"])\n    # A monitor can be attached, detached, or rearranged while the app runs.\n    # Refresh immediately when the cached topology cannot map the cursor.\n    layout = refresh_monitor_layout(force=True)\n    for m in layout:\n        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:\n            return int(m["index"])\n    return None\n''',
        "monitor_at refresh",
    )

    text = replace_if_present(
        text,
        '''            # pynput reports Windows virtual-desktop coordinates, including\n            # negative coordinates for displays placed left/above primary.\n            if dist < 5000:\n                payload = {"cursor_distance_px":dist}\n                if last_monitor_index is not None and current_monitor is not None and current_monitor != last_monitor_index:\n                    payload["monitor_switches"] = 1\n                queue_input(**payload)\n''',
        '''            # Count the full Windows virtual-desktop movement. Large jumps\n            # are legitimate on 4K and multi-monitor layouts and must not be\n            # silently discarded. Negative X/Y coordinates are valid.\n            if math.isfinite(dist) and dist >= 0:\n                payload = {"cursor_distance_px":dist}\n                if last_monitor_index is not None and current_monitor is not None and current_monitor != last_monitor_index:\n                    payload["monitor_switches"] = 1\n                queue_input(**payload)\n''',
        "cursor distance limit",
    )

    marker = '''def tracker() -> None:\n'''
    recovery = '''def recover_stale_sessions() -> None:\n    """Close focus sessions left open by a crash or forced termination."""\n    conn = db()\n    now = datetime.now().isoformat(timespec="seconds")\n    conn.execute(\n        "UPDATE focus_sessions SET ended_at=COALESCE(ended_at, ?), ended_reason=CASE WHEN ended_reason='' THEN 'recovered' ELSE ended_reason END WHERE ended_at IS NULL",\n        (now,),\n    )\n    conn.commit()\n    conn.close()\n\n\ndef self_test() -> int:\n    """Offline smoke test used by the Windows release pipeline."""\n    try:\n        init_db()\n        recover_stale_sessions()\n        ensure_today()\n        if not (WEB / "index.html").is_file():\n            raise RuntimeError("web/index.html missing")\n        if not (WEB / "assets").is_dir():\n            raise RuntimeError("web/assets missing")\n        if not api.routes:\n            raise RuntimeError("FastAPI routes were not registered")\n        info = display_info()\n        if not isinstance(info.get("count"), int):\n            raise RuntimeError("display detection returned invalid data")\n        print("Pelican Workbench self-test: PASS")\n        return 0\n    except Exception as exc:\n        print(f"Pelican Workbench self-test: FAIL: {exc}")\n        return 1\n\n\n'''
    if "def self_test() -> int:" not in text:
        if marker not in text:
            raise RuntimeError("tracker marker not found")
        text = text.replace(marker, recovery + marker, 1)

    old_queries = '''    timeline=conn.execute("SELECT slice_start,category,seconds,events FROM activity_slices WHERE date(slice_start)=? ORDER BY slice_start", (today_key(),)).fetchall()\n    apps=conn.execute("SELECT category,seconds FROM app_usage WHERE day=? ORDER BY seconds DESC", (today_key(),)).fetchall()\n    sessions=conn.execute("SELECT id,started_at,ended_at,active_seconds,categories,ended_reason FROM focus_sessions WHERE date(started_at)=? ORDER BY started_at DESC", (today_key(),)).fetchall()\n'''
    new_queries = '''    timeline=conn.execute("SELECT slice_start,category,seconds,events FROM activity_slices WHERE date(slice_start) BETWEEN ? AND ? ORDER BY slice_start", (start.isoformat(), end.isoformat())).fetchall()\n    apps=conn.execute("SELECT category,COALESCE(SUM(seconds),0) AS seconds FROM app_usage WHERE day BETWEEN ? AND ? GROUP BY category ORDER BY seconds DESC", (start.isoformat(), end.isoformat())).fetchall()\n    sessions=conn.execute("SELECT id,started_at,ended_at,active_seconds,categories,ended_reason FROM focus_sessions WHERE date(started_at) BETWEEN ? AND ? ORDER BY started_at DESC", (start.isoformat(), end.isoformat())).fetchall()\n'''
    text = replace_if_present(text, old_queries, new_queries, "range queries")

    old_main = '''def main() -> None:\n    enforce_release_integrity()\n    init_db()\n    ensure_today()\n'''
    new_main = '''def main() -> None:\n    if "--self-test" in sys.argv:\n        raise SystemExit(self_test())\n    enforce_release_integrity()\n    init_db()\n    recover_stale_sessions()\n    ensure_today()\n'''
    text = replace_if_present(text, old_main, new_main, "main startup")
    return text


def main() -> None:
    source = APP.read_text(encoding="utf-8")
    repaired = repair(source)
    if repaired == source:
        print("Pelican Workbench source repair: already applied")
        return
    APP.write_text(repaired, encoding="utf-8", newline="\n")
    print("Pelican Workbench source repair: APPLIED")


if __name__ == "__main__":
    main()
