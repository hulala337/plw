"""Transactional upgrades for existing SQLite databases (schema version 1)."""

SCHEMA_VERSION = 1


def migrate(conn):
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise RuntimeError(
            "Database was created by a newer application; upgrade the application."
        )
    if version == SCHEMA_VERSION:
        return
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        # Migrate older databases that predate activity_events.
        daily_cols = {r[1] for r in conn.execute("PRAGMA table_info(daily)").fetchall()}
        if "activity_events" not in daily_cols:
            conn.execute(
                "ALTER TABLE daily ADD COLUMN activity_events INTEGER NOT NULL DEFAULT 0"
            )
        if "monitor_switches" not in daily_cols:
            conn.execute(
                "ALTER TABLE daily ADD COLUMN monitor_switches INTEGER NOT NULL DEFAULT 0"
            )
        todo_cols = {r[1] for r in conn.execute("PRAGMA table_info(todos)").fetchall()}
        if "completion_count" not in todo_cols:
            conn.execute(
                "ALTER TABLE todos ADD COLUMN completion_count INTEGER NOT NULL DEFAULT 0"
            )

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
            conn.execute(
                "INSERT OR IGNORE INTO activity_slices SELECT slice_start,category,seconds,events FROM activity_slices_mvp"
            )
            conn.execute("DROP TABLE activity_slices_mvp")
        conn.execute("PRAGMA user_version=1")
