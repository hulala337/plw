from __future__ import annotations

import csv
import io
import math
import os
import socket
import sys
import threading
import time
import webbrowser
from contextlib import suppress
from datetime import date, datetime, timedelta
from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pynput import keyboard, mouse
import uvicorn

try:
    import win32gui
    import win32process
    import winreg
    import win32api
except Exception:
    win32gui = win32process = winreg = win32api = None

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = ImageDraw = None

try:
    import webview
except Exception:
    webview = None

VERSION = (Path(__file__).resolve().parent / "VERSION.txt").read_text(encoding="utf-8").strip()
BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(BASE))) / "PelicanWorkbench"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "pelican.db"
WEB = BASE / "web"

try:
    from security.runtime_verify import verify_release_integrity
except Exception:
    verify_release_integrity = None

IDLE_SECONDS = 120
TRACK_INTERVAL = 1.0
FOCUS_BREAK_SECONDS = 120
LOCK = threading.RLock()
STOP = threading.Event()
PORT = 0

# FastAPI application must be created before any @api route decorators below.
api = FastAPI(title="Pelican Workbench", version=VERSION if "VERSION" in globals() else "3.6")

CATEGORY_LABELS = {
    "document": "文档编辑",
    "web": "网页检索",
    "excel": "Excel",
    "ppt": "PPT",
    "wechat": "微信",
    "meeting": "会议",
    "focus": "其他工作",
    "idle": "发呆 / 离开",
}
CATEGORY_ORDER = ["document", "web", "excel", "ppt", "wechat", "meeting", "focus", "idle"]
CATEGORY_ICONS = {"document": "▤", "web": "◌", "excel": "▦", "ppt": "◫", "wechat": "◉", "meeting": "◍", "focus": "✦", "idle": "☾"}

state = {
    "keys": 0, "text_chars": 0, "backspace": 0, "delete": 0, "enter": 0,
    "space": 0, "left_click": 0, "right_click": 0, "middle_click": 0,
    "scroll_events": 0, "scroll_distance_px": 0.0, "cursor_distance_px": 0.0,
    "activity_events": 0, "event_seq": 0,
}
last_xy: tuple[int, int] | None = None
last_monitor_index: tuple[int, int, int, int] | None = None
monitor_layout = []
monitor_layout_signature = ()
monitor_layout_ts = 0.0
last_input_ts = time.time()
listener_refs = []
listener_restart_lock = threading.Lock()
listener_last_ok = 0.0
listener_restart_count = 0
listener_error = ""
tracker_reset_seq = 0
listener_last_keyboard_event = 0.0
listener_last_mouse_event = 0.0
pending_lock = threading.Lock()
pending = {"keys":0,"text_chars":0,"backspace":0,"delete_count":0,"enter_count":0,"space_count":0,"left_click":0,"right_click":0,"middle_click":0,"scroll_events":0,"scroll_distance_px":0.0,"cursor_distance_px":0.0,"activity_events":0,"monitor_switches":0}
tray_icon = None
webview_window = None


class TodoIn(BaseModel):
    title: str


class TodoPatch(BaseModel):
    done: bool


class SettingsPatch(BaseModel):
    autostart: bool | None = None
    idle_seconds: int | None = None
    weather_enabled: bool | None = None
    desktop_pet: bool | None = None
    sounds_enabled: bool | None = None


def db() -> __import__("sqlite3").Connection:
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    with suppress(Exception):
        conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def enforce_release_integrity() -> None:
    # Source/developer runs may omit the signed security bundle. Frozen/compiled
    # releases must ship it; any protected asset change is treated as tampering.
    is_bundled = bool(getattr(sys, "frozen", False) or globals().get("__compiled__", False))
    if not is_bundled:
        return
    if verify_release_integrity is None:
        reason = "完整性校验模块不可用"
    else:
        ok, reason = verify_release_integrity(BASE)
        if ok:
            return
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"鹈鹕工作台启动被阻止。\n\n{reason}\n\n请从正版渠道重新安装。", "鹈鹕工作台 · 完整性保护", 0x10)
    except Exception:
        pass
    raise SystemExit(f"Pelican Workbench integrity check failed: {reason}")


def init_db() -> None:
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS daily (
            day TEXT PRIMARY KEY,
            keys INTEGER NOT NULL DEFAULT 0,
            text_chars INTEGER NOT NULL DEFAULT 0,
            backspace INTEGER NOT NULL DEFAULT 0,
            delete_count INTEGER NOT NULL DEFAULT 0,
            enter_count INTEGER NOT NULL DEFAULT 0,
            space_count INTEGER NOT NULL DEFAULT 0,
            left_click INTEGER NOT NULL DEFAULT 0,
            right_click INTEGER NOT NULL DEFAULT 0,
            middle_click INTEGER NOT NULL DEFAULT 0,
            scroll_events INTEGER NOT NULL DEFAULT 0,
            scroll_distance_px REAL NOT NULL DEFAULT 0,
            cursor_distance_px REAL NOT NULL DEFAULT 0,
            active_seconds REAL NOT NULL DEFAULT 0,
            idle_seconds REAL NOT NULL DEFAULT 0,
            activity_events INTEGER NOT NULL DEFAULT 0,
            monitor_switches INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS activity_slices (
            slice_start TEXT NOT NULL,
            category TEXT NOT NULL,
            seconds INTEGER NOT NULL DEFAULT 0,
            events INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(slice_start, category)
        );
        CREATE TABLE IF NOT EXISTS app_usage (
            day TEXT NOT NULL,
            category TEXT NOT NULL,
            seconds REAL NOT NULL DEFAULT 0,
            PRIMARY KEY(day, category)
        );
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            active_seconds REAL NOT NULL DEFAULT 0,
            break_seconds REAL NOT NULL DEFAULT 0,
            event_count INTEGER NOT NULL DEFAULT 0,
            categories TEXT NOT NULL DEFAULT '',
            ended_reason TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS progress_profile (
            id INTEGER PRIMARY KEY CHECK(id=1),
            xp INTEGER NOT NULL DEFAULT 0,
            total_active_seconds REAL NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS unlocks (
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            unlocked_at TEXT NOT NULL,
            PRIMARY KEY(item_type, item_id)
        );
        CREATE TABLE IF NOT EXISTS achievements (
            achievement_id TEXT PRIMARY KEY,
            unlocked_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS progress_events (event_key TEXT PRIMARY KEY,event_type TEXT NOT NULL,xp INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS equipment (
            slot TEXT PRIMARY KEY,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scenes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            required_level INTEGER NOT NULL DEFAULT 1,
            base_id TEXT NOT NULL DEFAULT 'office',
            weather TEXT NOT NULL DEFAULT 'clear',
            time_mode TEXT NOT NULL DEFAULT 'auto',
            monitor_mode TEXT NOT NULL DEFAULT 'auto'
        );
        CREATE TABLE IF NOT EXISTS pelicans (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            required_level INTEGER NOT NULL DEFAULT 1,
            body_id TEXT NOT NULL DEFAULT 'classic',
            outfit_id TEXT NOT NULL DEFAULT 'default'
        );
        CREATE TABLE IF NOT EXISTS outfits (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            required_level INTEGER NOT NULL DEFAULT 1,
            pelican_id TEXT,
            FOREIGN KEY(pelican_id) REFERENCES pelicans(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS accessories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            required_level INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS decorations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            required_level INTEGER NOT NULL DEFAULT 1,
            slot TEXT NOT NULL DEFAULT 'room'
        );
        CREATE TABLE IF NOT EXISTS effects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            required_level INTEGER NOT NULL DEFAULT 1
        );        """
    )
    # Migrate older databases that predate activity_events.
    daily_cols = {r[1] for r in conn.execute("PRAGMA table_info(daily)").fetchall()}
    if "activity_events" not in daily_cols:
        conn.execute("ALTER TABLE daily ADD COLUMN activity_events INTEGER NOT NULL DEFAULT 0")
    if "monitor_switches" not in daily_cols:
        conn.execute("ALTER TABLE daily ADD COLUMN monitor_switches INTEGER NOT NULL DEFAULT 0")

    # MVP compatibility: migrate an older one-column primary key if present.
    cols = conn.execute("PRAGMA table_info(activity_slices)").fetchall()
    pk_cols = [r for r in cols if r[5]]
    if len(pk_cols) == 1 and pk_cols[0][1] == "slice_start":
        conn.execute("ALTER TABLE activity_slices RENAME TO activity_slices_mvp")
        conn.execute("""CREATE TABLE activity_slices (
            slice_start TEXT NOT NULL,
            category TEXT NOT NULL,
            seconds INTEGER NOT NULL DEFAULT 0,
            events INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(slice_start, category)
        )""")
        conn.execute("INSERT OR IGNORE INTO activity_slices SELECT slice_start,category,seconds,events FROM activity_slices_mvp")
        conn.execute("DROP TABLE activity_slices_mvp")
    conn.commit(); conn.close()


def today_key() -> str:
    return date.today().isoformat()


def ensure_today(day: str | None = None) -> None:
    conn = db(); conn.execute("INSERT OR IGNORE INTO daily(day) VALUES(?)", (day or today_key(),)); conn.commit(); conn.close()


def setting_get(key: str, default: str = "") -> str:
    conn = db(); row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone(); conn.close()
    return default if not row else str(row["value"])


def setting_set(key: str, value: str) -> None:
    conn = db(); conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value)); conn.commit(); conn.close()


def mark_event() -> None:
    global last_input_ts
    last_input_ts = time.time()
    with LOCK:
        state["event_seq"] += 1


def queue_input(**kwargs) -> None:
    """Fast, exception-safe input hook path. SQLite is flushed by tracker()."""
    global last_input_ts
    now = time.time()
    last_input_ts = now
    with LOCK:
        state["event_seq"] += 1
    with pending_lock:
        for key, value in kwargs.items():
            if key in pending:
                pending[key] += value
        pending["activity_events"] += 1


def flush_pending() -> None:
    # Keep the batch queued until SQLite confirms the commit. A transient lock
    # must never turn input events into silent data loss.
    ensure_today()
    with pending_lock:
        batch = {k:v for k,v in pending.items() if v}
    if not batch:
        return
    with LOCK:
        conn = db()
        try:
            sets = ", ".join("%s=%s+?" % (k,k) for k in batch)
            conn.execute("UPDATE daily SET %s WHERE day=?" % sets, [*batch.values(), today_key()])
            conn.commit()
        except Exception:
            with suppress(Exception):
                conn.rollback()
            raise
        finally:
            conn.close()
    with pending_lock:
        for key, value in batch.items():
            pending[key] = max(0, pending[key] - value)


def persist_tracker_tick(day: str, slice_key: str, category: str, dt: float, events: int = 0) -> None:
    """Atomically persist one tracker tick and all queued input counters."""
    with LOCK:
        with pending_lock:
            batch = {k: v for k, v in pending.items() if v}
        conn = db()
        try:
            conn.execute("INSERT OR IGNORE INTO daily(day) VALUES(?)", (day,))
            conn.execute("INSERT OR IGNORE INTO progress_profile(id,xp,total_active_seconds,level,updated_at) VALUES(1,0,0,1,?)", (datetime.now().isoformat(timespec="seconds"),))
            updates = dict(batch)
            time_field = "active_seconds" if category != "idle" else "idle_seconds"
            updates[time_field] = updates.get(time_field, 0) + dt
            sets = ", ".join(f"{k}={k}+?" for k in updates)
            conn.execute(f"UPDATE daily SET {sets} WHERE day=?", [*updates.values(), day])
            if time_field == "active_seconds" and dt > 0:
                conn.execute("UPDATE progress_profile SET total_active_seconds=total_active_seconds+?,updated_at=? WHERE id=1",(dt,datetime.now().isoformat(timespec="seconds")))
            conn.execute(
                """INSERT INTO activity_slices(slice_start,category,seconds,events)
                   VALUES(?,?,?,?)
                   ON CONFLICT(slice_start,category) DO UPDATE
                   SET seconds=seconds+excluded.seconds,events=events+excluded.events""",
                (slice_key, category, int(round(dt)), events),
            )
            conn.execute(
                """INSERT INTO app_usage(day,category,seconds) VALUES(?,?,?)
                   ON CONFLICT(day,category) DO UPDATE SET seconds=seconds+excluded.seconds""",
                (day, category, dt),
            )
            conn.commit()
        except Exception:
            with suppress(Exception):
                conn.rollback()
            raise
        finally:
            conn.close()
    if batch:
        with pending_lock:
            for key, value in batch.items():
                pending[key] = max(0, pending[key] - value)


def incr(**kwargs) -> None:
    # Retained for non-hook bookkeeping; input hooks use queue_input().
    ensure_today()
    if not kwargs: return
    with LOCK:
        conn = db()
        sets = ", ".join(f"{k}={k}+?" for k in kwargs)
        conn.execute(f"UPDATE daily SET {sets} WHERE day=?", [*kwargs.values(), today_key()])
        conn.commit(); conn.close()


def key_is_text(key) -> bool:
    with suppress(Exception):
        ch = key.char
        return bool(ch) and (ch.isprintable() or ch == "\t")
    return False


def on_press(key) -> None:
    global listener_last_keyboard_event
    try:
        listener_last_keyboard_event = time.time()
        payload = {"keys": 1}
        if key == keyboard.Key.backspace: payload["backspace"] = 1
        elif key == keyboard.Key.delete: payload["delete_count"] = 1
        elif key == keyboard.Key.enter: payload["enter_count"] = 1
        elif key == keyboard.Key.space: payload["space_count"] = 1
        elif key_is_text(key): payload["text_chars"] = 1
        queue_input(**payload)
    except Exception:
        # Never let a callback exception terminate the global keyboard hook.
        return


def on_click(x, y, button, pressed) -> None:
    global listener_last_mouse_event
    if not pressed: return
    try:
        listener_last_mouse_event = time.time()
        if button == mouse.Button.left: queue_input(left_click=1)
        elif button == mouse.Button.right: queue_input(right_click=1)
        elif button == mouse.Button.middle: queue_input(middle_click=1)
    except Exception:
        return


def on_scroll(x, y, dx, dy) -> None:
    global listener_last_mouse_event
    try:
        listener_last_mouse_event = time.time()
        queue_input(scroll_events=1, scroll_distance_px=abs(dy) * 120)
    except Exception:
        return


def refresh_monitor_layout(force: bool = False) -> list[dict]:
    global monitor_layout, monitor_layout_signature, monitor_layout_ts, last_xy, last_monitor_index
    if not force and time.time() - monitor_layout_ts < 5:
        return monitor_layout
    monitors = []
    try:
        import win32api as _wapi
        for index, (_handle, _hdc, rect) in enumerate(_wapi.EnumDisplayMonitors()):
            left, top, right, bottom = map(int, rect)
            monitors.append({
                "index": index, "left": left, "top": top, "right": right, "bottom": bottom,
                "width": right-left, "height": bottom-top,
            })
    except Exception:
        monitors = []
    signature = tuple(sorted((m["left"], m["top"], m["right"], m["bottom"]) for m in monitors))
    if monitor_layout_signature and signature != monitor_layout_signature:
        last_xy = None
        last_monitor_index = None
    monitor_layout = monitors
    monitor_layout_signature = signature
    monitor_layout_ts = time.time()
    return monitor_layout

def monitor_at(x: int, y: int) -> tuple[int, int, int, int] | None:
    layout = refresh_monitor_layout()
    for m in layout:
        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:
            return (m["left"], m["top"], m["right"], m["bottom"])
    layout = refresh_monitor_layout(force=True)
    for m in layout:
        if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:
            return (m["left"], m["top"], m["right"], m["bottom"])
    return None
def on_move(x, y) -> None:
    global last_xy, last_monitor_index, listener_last_mouse_event
    try:
        listener_last_mouse_event = time.time()
        xi, yi = int(x), int(y)
        current_monitor = monitor_at(xi, yi)
        if last_xy is not None:
            dist = math.hypot(xi-last_xy[0], yi-last_xy[1])
            # Count the full Windows virtual-desktop movement. Large jumps are
            # legitimate on 4K and multi-monitor layouts and must not be dropped.
            if math.isfinite(dist) and dist >= 0:
                payload = {"cursor_distance_px":dist}
                if last_monitor_index is not None and current_monitor is not None and current_monitor != last_monitor_index:
                    payload["monitor_switches"] = 1
                queue_input(**payload)
        last_xy = (xi, yi)
        last_monitor_index = current_monitor
    except Exception:
        return


def foreground_context() -> tuple[str, str]:
    # Transient classification only: name/title are never persisted.
    if win32gui and win32process:
        with suppress(Exception):
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            return (proc.name() or "").lower(), win32gui.GetWindowText(hwnd) or ""
    return "", ""


def classify_activity(name: str, title: str, active: bool) -> str:
    if not active: return "idle"
    text = f"{name} {title}".lower()
    if any(k in text for k in ["teams.exe", "zoom.exe", "slack.exe", "meeting"]): return "meeting"
    if any(k in text for k in ["excel", "et.exe", "calc.exe", "libreoffice calc"]): return "excel"
    if any(k in text for k in ["powerpnt", "powerpoint", "wps演示", "wpp"]): return "ppt"
    if any(k in text for k in ["winword", "word", "wps", "writer", "libreoffice writer"]): return "document"
    if any(k in text for k in ["wechat", "weixin"]): return "wechat"
    if any(k in text for k in ["chrome", "msedge", "firefox", "brave", "opera", "arc.exe"]): return "web"
    return "focus"


def ops_from_row(row) -> int:
    return int((row["keys"] or 0)+(row["left_click"] or 0)+(row["right_click"] or 0)+(row["middle_click"] or 0)+(row["scroll_events"] or 0))


def longest_focus_for_range(start_day: date, end_day: date) -> int:
    conn = db(); rows = conn.execute("SELECT active_seconds FROM focus_sessions WHERE date(started_at)<=? AND (ended_at IS NULL OR date(ended_at)>=?)", (end_day.isoformat(), start_day.isoformat())).fetchall(); conn.close()
    return max([int(r["active_seconds"] or 0) for r in rows] or [0])


def work_rhythm(total, longest_focus: int) -> int:
    # An observational indicator rather than a productivity verdict.
    active = min(float(total.get("active_seconds", 0)) / (8*3600), 1)
    ops = min(ops_from_row(total) / 60000, 1)
    focus = min(longest_focus / 7200, 1)
    return round(active*40 + ops*25 + focus*35)


def range_bounds(kind: str) -> tuple[date, date]:
    end = date.today()
    if kind == "week": return end-timedelta(days=end.weekday()), end
    if kind == "month": return end.replace(day=1), end
    return end, end


def fetch_summary(start_day: date, end_day: date):
    conn = db(); rows = conn.execute("SELECT * FROM daily WHERE day BETWEEN ? AND ? ORDER BY day", (start_day.isoformat(), end_day.isoformat())).fetchall()
    fields = ["keys","text_chars","backspace","delete_count","enter_count","space_count","left_click","right_click","middle_click","scroll_events","scroll_distance_px","cursor_distance_px","active_seconds","idle_seconds","activity_events","monitor_switches"]
    total = {k:0 for k in fields}; by_day=[]
    for r in rows:
        d=dict(r); by_day.append(d)
        for k in fields: total[k] += d.get(k,0) or 0
    longest=longest_focus_for_range(start_day,end_day); rhythm=work_rhythm(total,longest)
    conn.close(); return total,by_day,longest,rhythm


def persist_slice(day: str, slice_key: str, category: str, dt: float, events: int = 0) -> None:
    with LOCK:
        conn=db()
        conn.execute("INSERT INTO activity_slices(slice_start,category,seconds,events) VALUES(?,?,?,?) ON CONFLICT(slice_start,category) DO UPDATE SET seconds=seconds+excluded.seconds,events=events+excluded.events", (slice_key,category,int(round(dt)),events))
        conn.execute("INSERT INTO app_usage(day,category,seconds) VALUES(?,?,?) ON CONFLICT(day,category) DO UPDATE SET seconds=seconds+excluded.seconds", (day,category,dt))
        conn.commit(); conn.close()


def _close_focus_session(session_id, session_started, session_active, session_last_active, session_events, categories, reason):
    if not session_id or not session_started: return
    end_dt = datetime.fromtimestamp(session_last_active or time.time()).isoformat(timespec="seconds")
    conn=db(); conn.execute("UPDATE focus_sessions SET ended_at=?,active_seconds=?,break_seconds=?,event_count=?,categories=?,ended_reason=? WHERE id=?", (end_dt,round(session_active),max(0,round(time.time()-(session_last_active or time.time()))),session_events,",".join(categories),reason,session_id)); conn.commit(); conn.close()


def recover_stale_sessions() -> None:
    """Close focus sessions left open by a crash or forced termination."""
    conn = db()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("UPDATE focus_sessions SET ended_at=COALESCE(ended_at, ?), ended_reason=CASE WHEN ended_reason='' THEN 'recovered' ELSE ended_reason END WHERE ended_at IS NULL", (now,))
    conn.commit()
    conn.close()


def self_test() -> int:
    """Offline + hook smoke test used by the Windows release pipeline."""
    try:
        init_db()
        recover_stale_sessions()
        ensure_today()
        if not (WEB / "index.html").is_file():
            raise RuntimeError("web/index.html missing")
        if not (WEB / "assets").is_dir():
            raise RuntimeError("web/assets missing")
        paths={getattr(route,"path","") for route in api.routes}
        required_paths={"/","/api/dashboard","/api/health","/api/display-info","/api/settings","/api/growth","/api/todos","/api/forget-today","/api/replay","/api/export/csv","/api/export/xlsx","/api/equipment"}
        missing=required_paths-paths
        if missing:
            raise RuntimeError("required API routes missing: "+", ".join(sorted(missing)))
        html=(WEB/"index.html").read_text(encoding="utf-8")
        js=(WEB/"assets"/"app.js").read_text(encoding="utf-8")
        if 'data-view="growth"' not in html or 'id="view-growth"' not in html:
            raise RuntimeError("Growth UI navigation/view missing")
        import re
        html_ids=set(re.findall(r'id="([^"]+)"',html))
        js_ids=set(re.findall(r"\$\('([^']+)'\)",js))
        missing_dom=sorted(js_ids-html_ids)
        if missing_dom:
            raise RuntimeError("frontend DOM contract missing IDs: "+", ".join(missing_dom))
        for view in ("home","replay","timeline","stats","growth","settings"):
            if f'id="view-{view}"' not in html:
                raise RuntimeError("frontend view missing: "+view)
        seed_progression_catalog()
        conn=db()
        required_tables={"progress_profile","progress_events","unlocks","achievements","equipment","scenes","pelicans","outfits","accessories","decorations","effects"}
        actual_tables={r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if required_tables-actual_tables:
            conn.close(); raise RuntimeError("P1 tables missing: "+", ".join(sorted(required_tables-actual_tables)))
        conn.close()
        gp=growth_payload()
        if not {"profile","collection","equipment","scenes","pelicans"}.issubset(gp):
            raise RuntimeError("P1 growth payload incomplete")
        if not any(x["id"]=="office" and x["unlocked"] for x in gp["scenes"]):
            raise RuntimeError("default scene not unlocked")
        if not any(x["id"]=="classic" and x["unlocked"] for x in gp["pelicans"]):
            raise RuntimeError("default pelican not unlocked")
        info = display_info()
        if not isinstance(info.get("count"), int):
            raise RuntimeError("display detection returned invalid data")

        # Verify that the actual pynput hooks can be created and remain alive.
        if not listeners_start():
            raise RuntimeError(f"input listeners failed to start: {listener_error}")
        time.sleep(0.35)
        if not listeners_healthy():
            raise RuntimeError(f"input listeners stopped immediately: {listener_error}")

        # Exercise the real hook -> pending -> SQLite path without writing
        # actual user input. Restore the exact daily row after verification.
        day = today_key()
        conn = db()
        before_row = conn.execute("SELECT * FROM daily WHERE day=?", (day,)).fetchone()
        if before_row is None:
            conn.close()
            raise RuntimeError("daily row missing")
        before = dict(before_row)
        conn.close()

        queue_input(keys=1, text_chars=1, cursor_distance_px=123.0, monitor_switches=1)
        persist_tracker_tick(day, datetime.now().replace(second=0,microsecond=0).isoformat(timespec="minutes"), "focus", 0.0, 1)
        conn = db()
        after = dict(conn.execute("SELECT * FROM daily WHERE day=?", (day,)).fetchone())
        expected = {"keys": 1, "text_chars": 1, "cursor_distance_px": 123.0, "activity_events": 1, "monitor_switches": 1}
        for key, delta in expected.items():
            if (after.get(key) or 0) != (before.get(key) or 0) + delta:
                raise RuntimeError("input pipeline persistence check failed: " + key)
        columns = [key for key in before if key != "day"]
        assignments = ", ".join("%s=?" % key for key in columns)
        conn.execute("UPDATE daily SET %s WHERE day=?" % assignments, [before[key] for key in columns] + [day])
        conn.commit()
        conn.close()
        print("Pelican Workbench self-test: PASS (DB + real hooks + display + web)")
        return 0
    except Exception as exc:
        print(f"Pelican Workbench self-test: FAIL: {exc}")
        return 1
    finally:
        for listener in list(listener_refs):
            with suppress(Exception):
                listener.stop()
        listener_refs.clear()


def tracker() -> None:
    global tracker_reset_seq
    prev=time.time(); session_id=None; session_started=None; session_active=0.0; session_last_active=None; last_seq=state["event_seq"]; session_events=0; categories=[]; local_reset_seq=tracker_reset_seq
    while not STOP.is_set():
        now=time.time(); dt=min(now-prev,5.0); active=(now-last_input_ts)<=int(setting_get("idle_seconds",str(IDLE_SECONDS)))
        if local_reset_seq != tracker_reset_seq:
            session_id=None; session_started=None; session_active=0.0; session_last_active=None; session_events=0; categories=[]; local_reset_seq=tracker_reset_seq
        name,title=foreground_context(); category=classify_activity(name,title,active)
        with LOCK: current_seq=state["event_seq"]
        new_events=max(0,current_seq-last_seq); last_seq=current_seq
        try:
            slice_key=datetime.now().replace(second=0,microsecond=0).isoformat(timespec="minutes")
            persist_tracker_tick(today_key(), slice_key, category, dt, new_events)
        except Exception:
            # A transient database failure must not kill the tracker thread.
            # Pending input remains queued by flush_pending() for a later retry.
            prev=now
            STOP.wait(TRACK_INTERVAL)
            continue
        try:
            if active:
                if session_id is None:
                    conn=db(); cur=conn.execute("INSERT INTO focus_sessions(started_at) VALUES(?)", (datetime.fromtimestamp(last_input_ts).isoformat(timespec="seconds"),)); session_id=cur.lastrowid; conn.commit(); conn.close()
                    session_started=last_input_ts; session_active=0; session_last_active=last_input_ts; session_events=0; categories=[]
                session_active += dt; session_last_active=last_input_ts; session_events += new_events
                if category not in categories: categories.append(category)
            else:
                if session_id and session_last_active and now-session_last_active > FOCUS_BREAK_SECONDS:
                    _close_focus_session(session_id,session_started,session_active,session_last_active,session_events,categories,"idle")
                    session_id=session_started=session_last_active=None; session_active=0; session_events=0; categories=[]
        except Exception:
            # Session bookkeeping must never terminate the tracker.
            prev=now
            STOP.wait(TRACK_INTERVAL)
            continue
        prev=now; STOP.wait(TRACK_INTERVAL)
    if session_id: _close_focus_session(session_id,session_started,session_active,session_last_active,session_events,categories,"shutdown")


def active_session() -> dict | None:
    conn=db(); row=conn.execute("SELECT * FROM focus_sessions WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1").fetchone(); conn.close()
    if not row: return None
    item=dict(row); item["live_seconds"]=max(0,round(time.time()-datetime.fromisoformat(item["started_at"]).timestamp())); return item


UNLOCK_CATALOG = [
    {"item_type":"decoration","item_id":"green_plant","name":"植物","description":"给工作室添一点绿色。","required_level":1},
    {"item_type":"decoration","item_id":"lamp","name":"台灯","description":"温柔的桌面灯光。","required_level":2},
    {"item_type":"decoration","item_id":"coffee_machine","name":"咖啡机","description":"工作室的咖啡补给站。","required_level":3},
    {"item_type":"scene","item_id":"dual_monitor_office","name":"双屏工作室","description":"适配双屏工作的专属布局。","required_level":4},
    {"item_type":"pelican","item_id":"coffee_pelican","name":"咖啡鹈鹕","description":"解锁咖啡主题鹈鹕。","required_level":5},
    {"item_type":"outfit","item_id":"coffee_outfit","name":"咖啡围裙","description":"咖啡主题服装。","required_level":5},
    {"item_type":"decoration","item_id":"fish_tank","name":"鱼缸","description":"工作间的小小水族箱。","required_level":6},
    {"item_type":"accessory","item_id":"headphones","name":"耳机","description":"专注时的工作配饰。","required_level":7},
    {"item_type":"scene","item_id":"sunset_office","name":"黄昏工作室","description":"黄昏时间模式。","required_level":8},
    {"item_type":"effect","item_id":"focus_sparkles","name":"专注星光","description":"专注工作时出现的轻微环境效果。","required_level":9},
    {"item_type":"decoration","item_id":"bookshelf","name":"书架","description":"让工作室更有生活感。","required_level":10},
]
ACHIEVEMENT_CATALOG = [
    {"id":"first_session","name":"第一次 Session","description":"累计有效工作达到 1 分钟。","condition":"active>=60","xp":25},
    {"id":"ten_hours","name":"累计 10 小时","description":"累计有效工作达到 10 小时。","condition":"active>=36000","xp":100},
    {"id":"hundred_hours","name":"累计 100 小时","description":"累计有效工作达到 100 小时。","condition":"active>=360000","xp":500},
    {"id":"multi_monitor","name":"多显示器","description":"检测到至少两块显示器。","condition":"monitors>=2","xp":50},
    {"id":"seven_day_streak","name":"连续 7 天","description":"连续 7 天每天有超过 1 分钟有效工作。","condition":"streak>=7","xp":100},
]

def progression_xp_from_events(conn) -> int:
    row=conn.execute("SELECT COALESCE(SUM(xp),0) AS xp FROM progress_events").fetchone()
    return int(row["xp"] or 0)

def award_progress_event(conn,event_key: str,event_type: str,xp: int,now: str) -> None:
    if xp>0: conn.execute("INSERT OR IGNORE INTO progress_events(event_key,event_type,xp,created_at) VALUES(?,?,?,?)",(event_key,event_type,int(xp),now))

def sync_progression() -> dict:
    """Materialize Growth from durable work facts and idempotent progression events."""
    conn=db()
    row=conn.execute("SELECT total_active_seconds FROM progress_profile WHERE id=1").fetchone()
    daily_active=float(conn.execute("SELECT COALESCE(SUM(active_seconds),0) AS active FROM daily").fetchone()["active"] or 0)
    if row is None:
        conn.execute("INSERT INTO progress_profile(id,xp,total_active_seconds,level,updated_at) VALUES(1,0,?,1,?)",(daily_active,datetime.now().isoformat(timespec="seconds")))
        active=daily_active
    else:
        active=float(row["total_active_seconds"] or 0)
        if active <= 0 and daily_active > 0:
            active=daily_active
            conn.execute("UPDATE progress_profile SET total_active_seconds=? WHERE id=1",(active,))
    chars=int(conn.execute("SELECT COALESCE(SUM(text_chars),0) AS chars FROM daily").fetchone()["chars"] or 0)
    now=datetime.now().isoformat(timespec="seconds")
    for r in conn.execute("SELECT id,completed_at FROM todos WHERE done=1 AND completed_at IS NOT NULL").fetchall():
        award_progress_event(conn,"todo:%s:completed"%r["id"],"todo",20,r["completed_at"] or now)
    for ach in ACHIEVEMENT_CATALOG:
        ready=(ach["id"]=="first_session" and active>=60) or (ach["id"]=="ten_hours" and active>=36000) or (ach["id"]=="hundred_hours" and active>=360000) or (ach["id"]=="multi_monitor" and len(refresh_monitor_layout())>=2) or (ach["id"]=="seven_day_streak" and streak_days()>=7)
        if ready:
            conn.execute("INSERT OR IGNORE INTO achievements(achievement_id,unlocked_at) VALUES(?,?)",(ach["id"],now))
            award_progress_event(conn,"achievement:"+ach["id"],"achievement",ach["xp"],now)
    xp=int(active/60.0)+progression_xp_from_events(conn); level=min(12,1+xp//600)
    conn.execute("""INSERT INTO progress_profile(id,xp,total_active_seconds,level,updated_at) VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET xp=excluded.xp,total_active_seconds=excluded.total_active_seconds,level=excluded.level,updated_at=excluded.updated_at""",(xp,active,level,now))
    for item in UNLOCK_CATALOG:
        if level>=item["required_level"]: conn.execute("INSERT OR IGNORE INTO unlocks(item_type,item_id,unlocked_at) VALUES(?,?,?)",(item["item_type"],item["item_id"],now))
    conn.commit()
    unlock_rows=conn.execute("SELECT item_type,item_id,unlocked_at FROM unlocks ORDER BY unlocked_at,item_type,item_id").fetchall()
    achievement_rows=conn.execute("SELECT achievement_id,unlocked_at FROM achievements ORDER BY unlocked_at,achievement_id").fetchall()
    conn.close()
    return {"xp":xp,"level":level,"active_hours":round(active/3600.0,2),"text_chars":chars,"unlocks":[dict(x) for x in unlock_rows],"achievements":[dict(x) for x in achievement_rows]}

def lifetime_stats() -> dict:
    p=sync_progression()
    return {"active_hours":p["active_hours"],"text_chars":p["text_chars"],"level":p["level"],
            "xp":p["xp"],"unlocked":[x["item_id"] for x in p["unlocks"]]}


def growth_payload() -> dict:
    p=sync_progression(); conn=db()
    tables={"scenes":"scenes","pelicans":"pelicans","outfits":"outfits","accessories":"accessories","decorations":"decorations","effects":"effects"}
    rows={k:[dict(x) for x in conn.execute("SELECT * FROM "+v+" ORDER BY required_level,id").fetchall()] for k,v in tables.items()}
    equipment=[dict(x) for x in conn.execute("SELECT * FROM equipment ORDER BY slot").fetchall()]
    conn.close(); unlocked={(x["item_type"],x["item_id"]) for x in p["unlocks"]}
    def decorate(items,kind): return [{**x,"unlocked":(kind,x["id"]) in unlocked or x["required_level"]<=1} for x in items]
    xp=p["xp"]; level=p["level"]; start=(level-1)*600; nxt=level*600 if level<12 else start; into=max(0,xp-start)
    return {"profile":{"xp":xp,"level":level,"active_hours":p["active_hours"],"level_xp_start":start,"next_level_xp":nxt,"xp_into_level":into,"xp_to_next_level":max(0,nxt-xp),"progress_pct":100 if level>=12 else round(min(1,into/max(1,nxt-start))*100,1)},
            "unlocks":p["unlocks"],"achievements":p["achievements"],
            "collection":{"pelicans":decorate(rows["pelicans"],"pelican"),"outfits":decorate(rows["outfits"],"outfit"),"accessories":decorate(rows["accessories"],"accessory"),"scenes":decorate(rows["scenes"],"scene"),"decorations":decorate(rows["decorations"],"decoration"),"effects":decorate(rows["effects"],"effect")},
            "scenes":decorate(rows["scenes"],"scene"),"pelicans":decorate(rows["pelicans"],"pelican"),"equipment":equipment}
def seed_progression_catalog() -> None:
    conn=db(); now=datetime.now().isoformat(timespec="seconds")
    conn.executemany("INSERT OR IGNORE INTO scenes(id,name,required_level,base_id,weather,time_mode,monitor_mode) VALUES(?,?,?,?,?,?,?)",[("office","基础工作室",1,"office","clear","auto","auto"),("dual_monitor_office","双屏工作室",4,"office","clear","auto","dual"),("sunset_office","黄昏工作室",8,"office","clear","dusk","auto")])
    conn.executemany("INSERT OR IGNORE INTO pelicans(id,name,required_level,body_id,outfit_id) VALUES(?,?,?,?,?)",[("classic","基础鹈鹕",1,"classic","default"),("coffee_pelican","咖啡鹈鹕",5,"classic","coffee")])
    conn.executemany("INSERT OR IGNORE INTO outfits(id,name,required_level,pelican_id) VALUES(?,?,?,?)",[("default","基础服装",1,"classic"),("coffee_outfit","咖啡围裙",5,"coffee_pelican")])
    conn.executemany("INSERT OR IGNORE INTO accessories(id,name,required_level) VALUES(?,?,?)",[("headphones","耳机",7)])
    conn.executemany("INSERT OR IGNORE INTO decorations(id,name,required_level,slot) VALUES(?,?,?,?)",[("green_plant","植物",1,"room"),("lamp","台灯",2,"desk"),("coffee_machine","咖啡机",3,"desk"),("fish_tank","鱼缸",6,"room"),("bookshelf","书架",10,"room")])
    conn.executemany("INSERT OR IGNORE INTO effects(id,name,required_level) VALUES(?,?,?)",[("focus_sparkles","专注星光",9)])
    for slot,item_type,item_id in [("scene","scene","office"),("pelican","pelican","classic"),("outfit","outfit","default")]:
        conn.execute("INSERT OR IGNORE INTO equipment(slot,item_type,item_id,updated_at) VALUES(?,?,?,?)",(slot,item_type,item_id,now))
    conn.commit(); conn.close()
def streak_days() -> int:
    conn=db(); rows=conn.execute("SELECT day,active_seconds FROM daily WHERE active_seconds>60 ORDER BY day DESC LIMIT 60").fetchall(); conn.close()
    streak=0; cursor=date.today()
    days={date.fromisoformat(r["day"]):r["active_seconds"] for r in rows}
    while cursor in days:
        streak+=1; cursor-=timedelta(days=1)
    return streak


def api_payload(kind="today") -> dict:
    start,end=range_bounds(kind); total,by_day,longest,rhythm=fetch_summary(start,end); conn=db()
    timeline=conn.execute("SELECT slice_start,category,seconds,events FROM activity_slices WHERE date(slice_start) BETWEEN ? AND ? ORDER BY slice_start", (start.isoformat(), end.isoformat())).fetchall()
    apps=conn.execute("SELECT category,COALESCE(SUM(seconds),0) AS seconds FROM app_usage WHERE day BETWEEN ? AND ? GROUP BY category ORDER BY seconds DESC", (start.isoformat(), end.isoformat())).fetchall()
    sessions=conn.execute("SELECT id,started_at,ended_at,active_seconds,categories,ended_reason FROM focus_sessions WHERE started_at < ? AND (ended_at IS NULL OR ended_at >= ?) ORDER BY started_at DESC", ((end+timedelta(days=1)).isoformat(), start.isoformat())).fetchall()
    todos=conn.execute("SELECT id,title,done,created_at,completed_at FROM todos ORDER BY done ASC,id DESC").fetchall(); conn.close()
    world = growth_payload()
    return {"version":VERSION,"range":kind,"summary":total,"display":display_info(),"days":by_day,"longest_focus_seconds":longest,"rhythm":rhythm,"timeline":[dict(x) for x in timeline],"apps":[dict(x) for x in apps],"sessions":[dict(x) for x in sessions],"active_session":active_session(),"todos":[dict(x) for x in todos],"lifetime":lifetime_stats(),"streak":streak_days(),"world":{"equipment":world["equipment"],"scenes":world["scenes"],"pelicans":world["pelicans"]},"privacy":{"stores_actual_input":False,"stores_window_titles":False,"stores_urls":False,"local_only":True}}


def startup_enabled() -> bool:
    if not winreg: return False
    with suppress(Exception):
        key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_READ); val,_=winreg.QueryValueEx(key,"PelicanWorkbench"); winreg.CloseKey(key); return bool(val)
    return False


def app_launch_command() -> str:
    exe=Path(sys.executable); script=Path(__file__).resolve()
    if exe.name.lower().startswith("python"): return f'"{exe}" "{script}" --tray'
    return f'"{exe}" --tray'


def set_startup(enabled: bool) -> bool:
    if not winreg: return False
    key=winreg.CreateKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run")
    if enabled: winreg.SetValueEx(key,"PelicanWorkbench",0,winreg.REG_SZ,app_launch_command())
    else:
        with suppress(FileNotFoundError): winreg.DeleteValue(key,"PelicanWorkbench")
    winreg.CloseKey(key); return startup_enabled()


def make_tray_image():
    if Image is None: return None
    im=Image.new("RGBA",(64,64),(24,43,63,255)); d=ImageDraw.Draw(im)
    d.ellipse((8,10,48,53),fill=(248,248,241),outline=(117,157,179),width=2); d.polygon([(34,27),(60,34),(36,43)],fill=(241,155,31)); d.ellipse((25,20,29,24),fill=(28,44,54)); d.arc((12,28,38,53),20,140,fill=(206,218,224),width=3); return im


def run_server() -> int:
    global PORT
    sock=socket.socket(); sock.bind(("127.0.0.1",0)); PORT=sock.getsockname()[1]; sock.close()
    threading.Thread(target=uvicorn.run,kwargs={"app":api,"host":"127.0.0.1","port":PORT,"log_level":"warning"},daemon=True).start(); return PORT


def wait_for_server(timeout: float = 5.0) -> bool:
    deadline=time.time()+timeout
    while time.time() < deadline:
        with suppress(Exception):
            sock=socket.create_connection(("127.0.0.1",PORT),timeout=0.25); sock.close(); return True
        time.sleep(0.05)
    return False


def open_ui() -> bool:
    global webview_window
    url=f"http://127.0.0.1:{PORT}/"
    if webview:
        if webview_window:
            with suppress(Exception): webview_window.show(); webview_window.restore(); webview_window.bring_to_front()
            return
        try:
            webview_window=webview.create_window("鹈鹕工作台",url,width=1520,height=960,min_size=(1120,720),background_color="#eef4f8")

            def on_closing():
                # Closing the main window should minimize to the tray. Only the
                # tray's Quit command is allowed to actually destroy the window.
                if STOP.is_set():
                    return True
                with suppress(Exception):
                    webview_window.hide()
                return False

            webview_window.events.closing += on_closing
            webview.start(gui="edgechromium",debug=False)
            return True
        except Exception:
            # WebView2 may be missing/broken on a fresh Windows machine. Keep
            # the application useful by opening the local dashboard in the
            # default browser instead of silently leaving only a tray icon.
            with suppress(Exception):
                webbrowser.open(url)
            return False
    webbrowser.open(url)
    return False


def start_tray() -> None:
    """Run the Windows tray icon loop.

    pywebview's GUI loop must stay on the main thread on Windows, so the
    tray loop is deliberately hosted in a background thread for normal UI
    launches.  The tray-only startup path still uses this function directly.
    """
    global tray_icon
    if not pystray:
        return

    def quit_app(icon, item):
        STOP.set()
        with suppress(Exception):
            if webview_window:
                webview_window.destroy()
        with suppress(Exception):
            icon.stop()

    def show_app(icon, item):
        # pywebview APIs are safe to request from the tray callback for an
        # already-running window. If no window exists, ask the main/UI thread
        # to create it instead of starting a second GUI loop in the tray thread.
        if webview_window:
            with suppress(Exception):
                webview_window.show()
                webview_window.restore()
                webview_window.bring_to_front()
        else:
            threading.Thread(target=open_ui, daemon=True, name="ui-request").start()

    menu = pystray.Menu(
        pystray.MenuItem("打开鹈鹕工作台", show_app, default=True),
        pystray.MenuItem("开机启动", lambda icon, item: set_startup(not startup_enabled())),
        pystray.MenuItem("退出程序", quit_app),
    )
    tray_icon = pystray.Icon("PelicanWorkbench", make_tray_image(), "鹈鹕工作台", menu)
    tray_icon.run()


def set_windows_dpi_awareness() -> None:
    """Keep pynput and Win32 monitor coordinates in the same physical-pixel space."""
    if os.name != "nt":
        return
    with suppress(Exception):
        import ctypes
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
            return
    with suppress(Exception):
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()

def listeners_start() -> bool:
    global listener_refs, listener_last_ok, listener_error
    new_refs = []
    try:
        k=keyboard.Listener(on_press=on_press)
        m=mouse.Listener(on_click=on_click,on_scroll=on_scroll,on_move=on_move)
        new_refs=[k,m]
        k.start(); m.start()
        listener_refs=new_refs
        listener_last_ok=time.time()
        listener_error=""
        return True
    except Exception as exc:
        listener_error=f"{type(exc).__name__}: {exc}"
        # Stop both locally-created hooks even if the second hook failed after
        # the first one had already started. This prevents an orphaned global
        # keyboard hook and makes watchdog recovery deterministic.
        for listener in new_refs:
            with suppress(Exception):
                listener.stop()
        listener_refs=[]
        return False


def listeners_healthy() -> bool:
    return len(listener_refs) == 2 and all(
        bool(getattr(listener, "is_alive", lambda: False)())
        for listener in listener_refs
    )


def listener_watchdog() -> None:
    # Frozen Windows builds can lose an input hook without taking down the
    # application.  Check the hooks periodically and recreate them if needed.
    global listener_restart_count, listener_last_ok
    while not STOP.wait(5):
        if listeners_healthy():
            listener_last_ok=time.time()
            continue
        with listener_restart_lock:
            if listeners_healthy():
                continue
            if listeners_start():
                listener_restart_count += 1


def display_info() -> dict:
    monitors = []
    if win32api is not None:
        try:
            for m in refresh_monitor_layout(force=True):
                monitors.append(dict(m))
        except Exception:
            monitors = []
    if not monitors and os.name == "nt":
        with suppress(Exception):
            import ctypes
            user32=ctypes.windll.user32
            monitors=[{"name":"PRIMARY","left":0,"top":0,"right":user32.GetSystemMetrics(0),"bottom":user32.GetSystemMetrics(1),"width":user32.GetSystemMetrics(0),"height":user32.GetSystemMetrics(1)}]
    return {"count":len(monitors),"mode":"single" if len(monitors)<=1 else "multi","monitors":monitors}


@api.get("/api/display-info")
def api_display_info():
    return display_info()


@api.get("/api/health")
def api_health():
    return {
        "status": "ok" if listeners_healthy() else "degraded",
        "listeners": listeners_healthy(),
        "keyboard_listener": bool(listener_refs and len(listener_refs) >= 1 and listener_refs[0].is_alive()),
        "mouse_listener": bool(listener_refs and len(listener_refs) >= 2 and listener_refs[1].is_alive()),
        "tracker": any(t.name == "tracker" and t.is_alive() for t in threading.enumerate()),
        "database": DB_PATH.exists(),
        "last_listener_ok": listener_last_ok,
        "last_keyboard_event": listener_last_keyboard_event,
        "last_mouse_event": listener_last_mouse_event,
        "listener_restarts": listener_restart_count,
        "listener_error": listener_error,
    }


def export_rows(start: date,end: date):
    conn=db(); daily=conn.execute("SELECT * FROM daily WHERE day BETWEEN ? AND ? ORDER BY day",(start.isoformat(),end.isoformat())).fetchall(); tl=conn.execute("SELECT slice_start,category,seconds FROM activity_slices WHERE date(slice_start) BETWEEN ? AND ? ORDER BY slice_start",(start.isoformat(),end.isoformat())).fetchall(); apps=conn.execute("SELECT day,category,seconds FROM app_usage WHERE day BETWEEN ? AND ? ORDER BY day,seconds DESC",(start.isoformat(),end.isoformat())).fetchall(); sessions=conn.execute("SELECT * FROM focus_sessions WHERE started_at < ? AND (ended_at IS NULL OR ended_at >= ?) ORDER BY started_at",((end+timedelta(days=1)).isoformat(),start.isoformat())).fetchall(); conn.close(); return daily,tl,apps,sessions


api.mount("/assets",StaticFiles(directory=str(WEB/"assets")),name="assets")

@api.get("/")
def index(): return FileResponse(WEB/"index.html")

@api.get("/api/growth")
def growth():
    return growth_payload()


class EquipmentPatch(BaseModel):
    slot: str
    item_id: str

@api.patch("/api/equipment")
def patch_equipment(item: EquipmentPatch):
    slot=item.slot.strip().lower()
    allowed={"scene":"scenes","pelican":"pelicans","outfit":"outfits","accessory":"accessories","decoration":"decorations","effect":"effects"}
    if slot not in allowed: raise HTTPException(400,"不支持的装备槽位")
    conn=db(); row=conn.execute("SELECT id,required_level FROM "+allowed[slot]+" WHERE id=?",(item.item_id,)).fetchone()
    if not row: conn.close(); raise HTTPException(404,"内容不存在")
    profile=conn.execute("SELECT level FROM progress_profile WHERE id=1").fetchone(); level=int(profile["level"] if profile else 1)
    unlocked=conn.execute("SELECT 1 FROM unlocks WHERE item_type=? AND item_id=?",(slot,item.item_id)).fetchone()
    if not unlocked and int(row["required_level"] or 1)>level: conn.close(); raise HTTPException(403,"内容尚未解锁")
    now=datetime.now().isoformat(timespec="seconds")
    conn.execute("INSERT INTO equipment(slot,item_type,item_id,updated_at) VALUES(?,?,?,?) ON CONFLICT(slot) DO UPDATE SET item_type=excluded.item_type,item_id=excluded.item_id,updated_at=excluded.updated_at",(slot,slot,item.item_id,now))
    conn.commit(); equipment=[dict(x) for x in conn.execute("SELECT * FROM equipment ORDER BY slot").fetchall()]; conn.close()
    return {"ok":True,"equipment":equipment}
@api.get("/api/dashboard")
def dashboard(range: str="today"):
    if range not in {"today","week","month"}: raise HTTPException(400,"invalid range")
    return api_payload(range)

@api.get("/api/settings")
def get_settings():
    return {"version":VERSION,"autostart":startup_enabled(),"idle_seconds":int(setting_get("idle_seconds",str(IDLE_SECONDS))),"weather_enabled":setting_get("weather_enabled","1")!="0","desktop_pet":setting_get("desktop_pet","1")!="0","sounds_enabled":setting_get("sounds_enabled","0")!="0","privacy":{"local_only":True,"actual_input":False,"window_titles":False,"urls":False}}

@api.patch("/api/settings")
def patch_settings(item: SettingsPatch):
    if item.autostart is not None: set_startup(bool(item.autostart))
    if item.idle_seconds is not None: setting_set("idle_seconds",str(max(30,min(900,int(item.idle_seconds)))))
    if item.weather_enabled is not None: setting_set("weather_enabled","1" if item.weather_enabled else "0")
    if item.desktop_pet is not None: setting_set("desktop_pet","1" if item.desktop_pet else "0")
    if item.sounds_enabled is not None: setting_set("sounds_enabled","1" if item.sounds_enabled else "0")
    return get_settings()

@api.post("/api/todos")
def add_todo(item: TodoIn):
    title=item.title.strip()
    if not title: raise HTTPException(400,"任务不能为空")
    conn=db(); cur=conn.execute("INSERT INTO todos(title,created_at) VALUES(?,?)",(title,datetime.now().isoformat(timespec="seconds"))); conn.commit(); tid=cur.lastrowid; conn.close(); return {"id":tid,"title":title,"done":0}

@api.patch("/api/todos/{todo_id}")
def toggle_todo(todo_id:int,item:TodoPatch):
    completed=datetime.now().isoformat(timespec="seconds") if item.done else None; conn=db(); cur=conn.execute("UPDATE todos SET done=?,completed_at=? WHERE id=?",(1 if item.done else 0,completed,todo_id)); conn.commit(); conn.close();
    if not cur.rowcount: raise HTTPException(404,"任务不存在")
    return {"ok":True}

@api.delete("/api/todos/{todo_id}")
def delete_todo(todo_id:int):
    conn=db(); cur=conn.execute("DELETE FROM todos WHERE id=?",(todo_id,)); conn.commit(); conn.close();
    if not cur.rowcount: raise HTTPException(404,"任务不存在")
    return {"ok":True}

@api.post("/api/forget-today")
def forget_today():
    global last_input_ts, last_xy, last_monitor_index, tracker_reset_seq
    target=today_key()
    start=target+"T00:00:00"
    end=(date.today()+timedelta(days=1)).isoformat()+"T00:00:00"
    with pending_lock:
        for key in pending:
            pending[key]=0
    last_input_ts=0.0
    last_xy=None; last_monitor_index=None; tracker_reset_seq += 1
    conn=db()
    conn.execute("DELETE FROM daily WHERE day=?",(target,))
    conn.execute("DELETE FROM activity_slices WHERE date(slice_start)=?",(target,))
    conn.execute("DELETE FROM app_usage WHERE day=?",(target,))
    # Remove any focus session that overlaps today, including cross-midnight
    # sessions, so forgotten activity cannot remain visible in session history.
    conn.execute("DELETE FROM focus_sessions WHERE started_at < ? AND (ended_at IS NULL OR ended_at >= ?)",(end,start))
    conn.commit(); conn.close(); ensure_today(target)
    return {"ok":True,"day":target}

@api.get("/api/replay")
def replay(day:str|None=None):
    target=day or today_key(); conn=db(); rows=conn.execute("SELECT slice_start,category,seconds,events FROM activity_slices WHERE date(slice_start)=? ORDER BY slice_start",(target,)).fetchall(); conn.close();
    return {"day":target,"events":[dict(r) for r in rows]}

@api.get("/api/export/csv")
def export_csv(range:str="today"):
    start,end=range_bounds(range if range in {"today","week","month"} else "today"); daily,tl,apps,sessions=export_rows(start,end); out=io.StringIO(); w=csv.writer(out); w.writerow(["类型","日期/时间","分类","秒数","键盘","字符数","左键","右键","中键","滚轮","光标像素","活跃秒","空闲秒","行为事件","跨屏次数","会话分类","结束原因"])
    for r in daily:w.writerow(["daily",r["day"],"","",r["keys"],r["text_chars"],r["left_click"],r["right_click"],r["middle_click"],r["scroll_events"],round(r["cursor_distance_px"]),round(r["active_seconds"]),round(r["idle_seconds"]),r["activity_events"],r["monitor_switches"],"",""])
    for r in tl:w.writerow(["timeline",r["slice_start"],CATEGORY_LABELS.get(r["category"],r["category"]),r["seconds"],"","","","","","","","","","",""])
    for r in apps:w.writerow(["usage",r["day"],CATEGORY_LABELS.get(r["category"],r["category"]),round(r["seconds"]),"","","","","","","","","","",""])
    for r in sessions:w.writerow(["focus_session",r["started_at"],"",round(r["active_seconds"]),"","","","","","","","","",r["categories"],r["ended_reason"]])
    data=out.getvalue().encode("utf-8-sig"); return StreamingResponse(io.BytesIO(data),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="pelican_{range}.csv"'})

@api.get("/api/export/xlsx")
def export_xlsx(range:str="today"):
    from openpyxl import Workbook
    start,end=range_bounds(range if range in {"today","week","month"} else "today"); daily,tl,apps,sessions=export_rows(start,end); wb=Workbook(); ws=wb.active; ws.title="日报"; ws.append(["日期","键盘","输入字符数","鼠标左键","鼠标右键","滚轮","鼠标移动(px)","活跃(s)","空闲(s)","行为事件","跨屏次数"])
    for r in daily:ws.append([r["day"],r["keys"],r["text_chars"],r["left_click"],r["right_click"],r["scroll_events"],round(r["cursor_distance_px"]),round(r["active_seconds"]),round(r["idle_seconds"]),r["activity_events"],r["monitor_switches"]])
    ws2=wb.create_sheet("时间轴"); ws2.append(["时间","分类","秒数"])
    for r in tl:ws2.append([r["slice_start"],CATEGORY_LABELS.get(r["category"],r["category"]),r["seconds"]])
    ws3=wb.create_sheet("专注Session"); ws3.append(["开始","结束","活跃秒","分类序列","结束原因"])
    for r in sessions:ws3.append([r["started_at"],r["ended_at"],r["active_seconds"],r["categories"],r["ended_reason"]])
    ws4=wb.create_sheet("工作类型"); ws4.append(["日期","分类","秒数"])
    for r in apps:ws4.append([r["day"],CATEGORY_LABELS.get(r["category"],r["category"]),round(r["seconds"])])
    mem=io.BytesIO(); wb.save(mem); mem.seek(0); return StreamingResponse(mem,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="pelican_{range}.xlsx"'})


def main() -> None:
    enforce_release_integrity()
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    init_db()
    seed_progression_catalog()
    recover_stale_sessions()
    ensure_today()
    set_windows_dpi_awareness()
    run_server()
    if not wait_for_server():
        raise SystemExit("Pelican Workbench local server failed to start")
    if not listeners_start():
        # Do not pretend input tracking is active. The watchdog will retry and
        # the dashboard health indicator exposes the actual failure reason.
        pass
    threading.Thread(target=tracker, daemon=True, name="tracker").start()
    threading.Thread(target=listener_watchdog, daemon=True, name="listener-watchdog").start()

    # IMPORTANT: pywebview/EdgeChromium must own the Windows GUI event loop
    # on the main thread. The previous V3.2 implementation ran pystray on the
    # main thread and attempted to start pywebview from a tray worker, which
    # leaves the installed app with only a tray icon and no main window.
    #
    # Normal launch: tray in background + webview on the main thread.
    # --tray launch (used by Windows startup) intentionally stays tray-only.
    if "--tray" in sys.argv:
        start_tray()
    elif os.name == "nt" and pystray:
        tray_thread = threading.Thread(target=start_tray, daemon=True, name="tray")
        tray_thread.start()
        ui_owned_loop = open_ui()
        if ui_owned_loop:
            STOP.set()
        else:
            while not STOP.wait(0.5):
                pass
    else:
        ui_owned_loop = open_ui()
        if ui_owned_loop:
            STOP.set()
        else:
            while not STOP.wait(0.5):
                pass


if __name__=="__main__": main()
