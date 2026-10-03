from __future__ import annotations

from . import runtime


def db() -> __import__("sqlite3").Connection:
    import sqlite3

    conn = sqlite3.connect(runtime.DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    with runtime.suppress(Exception):
        conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    from . import database
    from workbench.migrations import SCHEMA_VERSION

    conn = database.db()
    if conn.execute("PRAGMA user_version").fetchone()[0] > SCHEMA_VERSION:
        conn.close()
        raise RuntimeError(
            "Database was created by a newer application; upgrade the application."
        )
    from .schema import SCHEMA_SQL

    conn.executescript(SCHEMA_SQL)
    from workbench.migrations import migrate

    try:
        migrate(conn)
    finally:
        conn.close()


def ensure_today(day: str | None = None) -> None:
    from . import database, services

    conn = database.db()
    conn.execute(
        "INSERT OR IGNORE INTO daily(day) VALUES(?)", (day or services.today_key(),)
    )
    conn.commit()
    conn.close()


def setting_get(key: str, default: str = "") -> str:
    from . import database

    conn = database.db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return default if not row else str(row["value"])


def setting_set(key: str, value: str) -> None:
    from . import database

    conn = database.db()
    conn.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def fetch_summary(start_day: runtime.date, end_day: runtime.date):
    from . import database, services

    conn = database.db()
    rows = conn.execute(
        "SELECT * FROM daily WHERE day BETWEEN ? AND ? ORDER BY day",
        (start_day.isoformat(), end_day.isoformat()),
    ).fetchall()
    fields = [
        "keys",
        "text_chars",
        "backspace",
        "delete_count",
        "enter_count",
        "space_count",
        "left_click",
        "right_click",
        "middle_click",
        "scroll_events",
        "scroll_distance_px",
        "cursor_distance_px",
        "active_seconds",
        "idle_seconds",
        "activity_events",
        "monitor_switches",
    ]
    total = {k: 0 for k in fields}
    by_day = []
    for r in rows:
        d = dict(r)
        by_day.append(d)
        for k in fields:
            total[k] += d.get(k, 0) or 0
    longest = services.longest_focus_for_range(start_day, end_day)
    rhythm = services.work_rhythm(total, longest)
    conn.close()
    return (total, by_day, longest, rhythm)


def persist_slice(
    day: str, slice_key: str, category: str, dt: float, events: int = 0
) -> None:
    from . import database

    with runtime.LOCK:
        conn = database.db()
        conn.execute(
            "INSERT INTO activity_slices(slice_start,category,seconds,events) VALUES(?,?,?,?) ON CONFLICT(slice_start,category) DO UPDATE SET seconds=seconds+excluded.seconds,events=events+excluded.events",
            (slice_key, category, int(round(dt)), events),
        )
        conn.execute(
            "INSERT INTO app_usage(day,category,seconds) VALUES(?,?,?) ON CONFLICT(day,category) DO UPDATE SET seconds=seconds+excluded.seconds",
            (day, category, dt),
        )
        conn.commit()
        conn.close()


def recover_stale_sessions() -> None:
    from . import database

    "Close focus sessions left open by a crash or forced termination."
    conn = database.db()
    now = runtime.datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE focus_sessions SET ended_at=COALESCE(ended_at, ?), ended_reason=CASE WHEN ended_reason='' THEN 'recovered' ELSE ended_reason END WHERE ended_at IS NULL",
        (now,),
    )
    conn.commit()
    conn.close()


def export_rows(start: runtime.date, end: runtime.date):
    from . import database

    conn = database.db()
    daily = conn.execute(
        "SELECT * FROM daily WHERE day BETWEEN ? AND ? ORDER BY day",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    tl = conn.execute(
        "SELECT slice_start,category,seconds FROM activity_slices WHERE date(slice_start) BETWEEN ? AND ? ORDER BY slice_start",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    apps = conn.execute(
        "SELECT day,category,seconds FROM app_usage WHERE day BETWEEN ? AND ? ORDER BY day,seconds DESC",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    sessions = conn.execute(
        "SELECT * FROM focus_sessions WHERE started_at < ? AND (ended_at IS NULL OR ended_at >= ?) ORDER BY started_at",
        ((end + runtime.timedelta(days=1)).isoformat(), start.isoformat()),
    ).fetchall()
    conn.close()
    return (daily, tl, apps, sessions)
