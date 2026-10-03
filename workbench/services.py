from __future__ import annotations

from . import runtime


def today_key() -> str:
    return runtime.date.today().isoformat()


def classify_activity(name: str, title: str, active: bool) -> str:
    if not active:
        return "idle"
    text = f"{name} {title}".lower()
    if any((k in text for k in ["teams.exe", "zoom.exe", "slack.exe", "meeting"])):
        return "meeting"
    if any((k in text for k in ["excel", "et.exe", "calc.exe", "libreoffice calc"])):
        return "excel"
    if any((k in text for k in ["powerpnt", "powerpoint", "wps演示", "wpp"])):
        return "ppt"
    if any(
        (k in text for k in ["winword", "word", "wps", "writer", "libreoffice writer"])
    ):
        return "document"
    if any((k in text for k in ["wechat", "weixin"])):
        return "wechat"
    if any(
        (
            k in text
            for k in ["chrome", "msedge", "firefox", "brave", "opera", "arc.exe"]
        )
    ):
        return "web"
    return "focus"


def ops_from_row(row) -> int:
    return int(
        (row["keys"] or 0)
        + (row["left_click"] or 0)
        + (row["right_click"] or 0)
        + (row["middle_click"] or 0)
        + (row["scroll_events"] or 0)
    )


def longest_focus_for_range(start_day: runtime.date, end_day: runtime.date) -> int:
    from . import database

    conn = database.db()
    rows = conn.execute(
        "SELECT active_seconds FROM focus_sessions WHERE date(started_at)<=? AND (ended_at IS NULL OR date(ended_at)>=?)",
        (end_day.isoformat(), start_day.isoformat()),
    ).fetchall()
    conn.close()
    return max([int(r["active_seconds"] or 0) for r in rows] or [0])


def work_rhythm(total, longest_focus: int) -> int:
    from . import services

    active = min(float(total.get("active_seconds", 0)) / (8 * 3600), 1)
    ops = min(services.ops_from_row(total) / 60000, 1)
    focus = min(longest_focus / 7200, 1)
    return round(active * 40 + ops * 25 + focus * 35)


def range_bounds(kind: str) -> tuple[runtime.date, runtime.date]:
    end = runtime.date.today()
    if kind == "week":
        return (end - runtime.timedelta(days=end.weekday()), end)
    if kind == "month":
        return (end.replace(day=1), end)
    return (end, end)


def active_session() -> dict | None:
    from . import database

    conn = database.db()
    row = conn.execute(
        "SELECT * FROM focus_sessions WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    item["live_seconds"] = max(0, round(float(item.get("active_seconds") or 0)))
    return item


def progression_xp_from_events(conn) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(xp),0) AS xp FROM progress_events"
    ).fetchone()
    return int(row["xp"] or 0)


def award_progress_event(
    conn, event_key: str, event_type: str, xp: int, now: str
) -> None:
    if xp > 0:
        conn.execute(
            "INSERT OR IGNORE INTO progress_events(event_key,event_type,xp,created_at) VALUES(?,?,?,?)",
            (event_key, event_type, int(xp), now),
        )


def sync_progression() -> dict:
    from . import database, services, tracking

    "Materialize Growth from durable work facts and idempotent progression events."
    conn = database.db()
    row = conn.execute(
        "SELECT total_active_seconds FROM progress_profile WHERE id=1"
    ).fetchone()
    daily_active = float(
        conn.execute(
            "SELECT COALESCE(SUM(active_seconds),0) AS active FROM daily"
        ).fetchone()["active"]
        or 0
    )
    if row is None:
        conn.execute(
            "INSERT INTO progress_profile(id,xp,total_active_seconds,level,updated_at) VALUES(1,0,?,1,?)",
            (daily_active, runtime.datetime.now().isoformat(timespec="seconds")),
        )
        active = daily_active
    else:
        active = float(row["total_active_seconds"] or 0)
        if active <= 0 and daily_active > 0:
            active = daily_active
            conn.execute(
                "UPDATE progress_profile SET total_active_seconds=? WHERE id=1",
                (active,),
            )
    chars = int(
        conn.execute(
            "SELECT COALESCE(SUM(text_chars),0) AS chars FROM daily"
        ).fetchone()["chars"]
        or 0
    )
    now = runtime.datetime.now().isoformat(timespec="seconds")
    for r in conn.execute(
        "SELECT id,completed_at,completion_count FROM todos WHERE done=1 AND completed_at IS NOT NULL AND completion_count>0"
    ).fetchall():
        services.award_progress_event(
            conn,
            "todo:%s:completed:%s" % (r["id"], r["completion_count"]),
            "todo",
            20,
            r["completed_at"] or now,
        )
    for ach in runtime.ACHIEVEMENT_CATALOG:
        ready = (
            ach["id"] == "first_session"
            and active >= 60
            or (ach["id"] == "ten_hours" and active >= 36000)
            or (ach["id"] == "hundred_hours" and active >= 360000)
            or (
                ach["id"] == "multi_monitor"
                and len(tracking.refresh_monitor_layout()) >= 2
            )
            or (ach["id"] == "seven_day_streak" and services.streak_days() >= 7)
        )
        if ready:
            conn.execute(
                "INSERT OR IGNORE INTO achievements(achievement_id,unlocked_at) VALUES(?,?)",
                (ach["id"], now),
            )
            services.award_progress_event(
                conn, "achievement:" + ach["id"], "achievement", ach["xp"], now
            )
    xp = int(active / 60.0) + services.progression_xp_from_events(conn)
    level = min(12, 1 + xp // 600)
    conn.execute(
        "INSERT INTO progress_profile(id,xp,total_active_seconds,level,updated_at) VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET xp=excluded.xp,total_active_seconds=excluded.total_active_seconds,level=excluded.level,updated_at=excluded.updated_at",
        (xp, active, level, now),
    )
    for item in runtime.UNLOCK_CATALOG:
        if level >= item["required_level"]:
            conn.execute(
                "INSERT OR IGNORE INTO unlocks(item_type,item_id,unlocked_at) VALUES(?,?,?)",
                (item["item_type"], item["item_id"], now),
            )
    conn.commit()
    unlock_rows = conn.execute(
        "SELECT item_type,item_id,unlocked_at FROM unlocks ORDER BY unlocked_at,item_type,item_id"
    ).fetchall()
    achievement_rows = conn.execute(
        "SELECT achievement_id,unlocked_at FROM achievements ORDER BY unlocked_at,achievement_id"
    ).fetchall()
    conn.close()
    return {
        "xp": xp,
        "level": level,
        "active_hours": round(active / 3600.0, 2),
        "text_chars": chars,
        "unlocks": [dict(x) for x in unlock_rows],
        "achievements": [dict(x) for x in achievement_rows],
    }


def lifetime_stats() -> dict:
    from . import services

    p = services.sync_progression()
    return {
        "active_hours": p["active_hours"],
        "text_chars": p["text_chars"],
        "level": p["level"],
        "xp": p["xp"],
        "unlocked": [x["item_id"] for x in p["unlocks"]],
    }


def growth_payload() -> dict:
    from . import database, services

    p = services.sync_progression()
    conn = database.db()
    tables = {
        "scenes": "scenes",
        "pelicans": "pelicans",
        "outfits": "outfits",
        "accessories": "accessories",
        "decorations": "decorations",
        "effects": "effects",
    }
    rows = {
        k: [
            dict(x)
            for x in conn.execute(
                "SELECT * FROM " + v + " ORDER BY required_level,id"
            ).fetchall()
        ]
        for k, v in tables.items()
    }
    equipment = [
        dict(x)
        for x in conn.execute("SELECT * FROM equipment ORDER BY slot").fetchall()
    ]
    conn.close()
    unlocked = {(x["item_type"], x["item_id"]) for x in p["unlocks"]}

    def decorate(items, kind):
        return [
            {**x, "unlocked": (kind, x["id"]) in unlocked or x["required_level"] <= 1}
            for x in items
        ]

    xp = p["xp"]
    level = p["level"]
    start = (level - 1) * 600
    nxt = level * 600 if level < 12 else start
    into = max(0, xp - start)
    return {
        "profile": {
            "xp": xp,
            "level": level,
            "active_hours": p["active_hours"],
            "level_xp_start": start,
            "next_level_xp": nxt,
            "xp_into_level": into,
            "xp_to_next_level": max(0, nxt - xp),
            "progress_pct": 100
            if level >= 12
            else round(min(1, into / max(1, nxt - start)) * 100, 1),
        },
        "unlocks": p["unlocks"],
        "achievements": p["achievements"],
        "unlock_catalog": [
            {**x, "unlocked": (x["item_type"], x["item_id"]) in unlocked}
            for x in runtime.UNLOCK_CATALOG
        ],
        "achievement_catalog": [
            {
                **x,
                "unlocked": x["id"] in {a["achievement_id"] for a in p["achievements"]},
            }
            for x in runtime.ACHIEVEMENT_CATALOG
        ],
        "collection": {
            "pelicans": decorate(rows["pelicans"], "pelican"),
            "outfits": decorate(rows["outfits"], "outfit"),
            "accessories": decorate(rows["accessories"], "accessory"),
            "scenes": decorate(rows["scenes"], "scene"),
            "decorations": decorate(rows["decorations"], "decoration"),
            "effects": decorate(rows["effects"], "effect"),
        },
        "scenes": decorate(rows["scenes"], "scene"),
        "pelicans": decorate(rows["pelicans"], "pelican"),
        "equipment": equipment,
    }


def seed_progression_catalog() -> None:
    from . import database

    conn = database.db()
    now = runtime.datetime.now().isoformat(timespec="seconds")
    conn.executemany(
        "INSERT OR IGNORE INTO scenes(id,name,required_level,base_id,weather,time_mode,monitor_mode) VALUES(?,?,?,?,?,?,?)",
        [
            ("office", "基础工作室", 1, "office", "clear", "auto", "auto"),
            ("dual_monitor_office", "双屏工作室", 4, "office", "clear", "auto", "dual"),
            ("sunset_office", "黄昏工作室", 8, "office", "clear", "dusk", "auto"),
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO pelicans(id,name,required_level,body_id,outfit_id) VALUES(?,?,?,?,?)",
        [
            ("classic", "基础鹈鹕", 1, "classic", "default"),
            ("coffee_pelican", "咖啡鹈鹕", 5, "classic", "coffee"),
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO outfits(id,name,required_level,pelican_id) VALUES(?,?,?,?)",
        [
            ("default", "基础服装", 1, "classic"),
            ("coffee_outfit", "咖啡围裙", 5, "coffee_pelican"),
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO accessories(id,name,required_level) VALUES(?,?,?)",
        [("headphones", "耳机", 7)],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO decorations(id,name,required_level,slot) VALUES(?,?,?,?)",
        [
            ("green_plant", "植物", 1, "room"),
            ("lamp", "台灯", 2, "desk"),
            ("coffee_machine", "咖啡机", 3, "desk"),
            ("fish_tank", "鱼缸", 6, "room"),
            ("bookshelf", "书架", 10, "room"),
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO effects(id,name,required_level) VALUES(?,?,?)",
        [("focus_sparkles", "专注星光", 9)],
    )
    for slot, item_type, item_id in [
        ("scene", "scene", "office"),
        ("pelican", "pelican", "classic"),
        ("outfit", "outfit", "default"),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO equipment(slot,item_type,item_id,updated_at) VALUES(?,?,?,?)",
            (slot, item_type, item_id, now),
        )
    conn.commit()
    conn.close()


def streak_days() -> int:
    from . import database

    conn = database.db()
    rows = conn.execute(
        "SELECT day,active_seconds FROM daily WHERE active_seconds>60 ORDER BY day DESC LIMIT 60"
    ).fetchall()
    conn.close()
    streak = 0
    cursor = runtime.date.today()
    days = {runtime.date.fromisoformat(r["day"]): r["active_seconds"] for r in rows}
    while cursor in days:
        streak += 1
        cursor -= runtime.timedelta(days=1)
    return streak


def world_payload() -> dict:
    from . import desktop
    return {"scene":"office","selected_scene":"office","pelican":"classic","outfit":"default","decorations":[],"display_count":desktop.display_info()["count"],"work_state":"working","pelican_state":"focused","time_phase":"day","weather_enabled":False,"weather_source":"disabled","desktop_pet":True}


def api_payload(kind="today") -> dict:
    from . import database, desktop, services

    start, end = services.range_bounds(kind)
    total, by_day, longest, rhythm = database.fetch_summary(start, end)
    conn = database.db()
    timeline = conn.execute(
        "SELECT slice_start,category,seconds,events FROM activity_slices WHERE date(slice_start) BETWEEN ? AND ? ORDER BY slice_start",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    apps = conn.execute(
        "SELECT category,COALESCE(SUM(seconds),0) AS seconds FROM app_usage WHERE day BETWEEN ? AND ? GROUP BY category ORDER BY seconds DESC",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    sessions = conn.execute(
        "SELECT id,started_at,ended_at,active_seconds,categories,ended_reason FROM focus_sessions WHERE started_at < ? AND (ended_at IS NULL OR ended_at >= ?) ORDER BY started_at DESC",
        ((end + runtime.timedelta(days=1)).isoformat(), start.isoformat()),
    ).fetchall()
    todos = conn.execute(
        "SELECT id,title,done,created_at,completed_at FROM todos ORDER BY done ASC,id DESC"
    ).fetchall()
    conn.close()
    from . import key_counts
    from . import characters
    confirmed = characters.summary(database.db, start.isoformat(), end.isoformat())
    keys_today = key_counts.top(database.db, services.today_key())
    return {
        "confirmed_characters": confirmed,
        "key_top_today": keys_today,
        "version": runtime.VERSION,
        "range": kind,
        "summary": total,
        "display": desktop.display_info(),
        "days": by_day,
        "longest_focus_seconds": longest,
        "rhythm": rhythm,
        "timeline": [dict(x) for x in timeline],
        "apps": [dict(x) for x in apps],
        "sessions": [dict(x) for x in sessions],
        "active_session": services.active_session(),
        "todos": [dict(x) for x in todos],
        "streak": services.streak_days(),
        "privacy": {
            "stores_actual_input": False,
            "stores_window_titles": False,
            "stores_urls": False,
            "local_only": database.setting_get("weather_enabled", "1") == "0",
            "weather_external": database.setting_get("weather_enabled", "1") != "0",
            "weather_provider": "Open-Meteo",
        },
    }
