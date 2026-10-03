"""Base SQLite schema; incremental upgrades live in migrations.py."""

SCHEMA_SQL = """
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
            completed_at TEXT,
            completion_count INTEGER NOT NULL DEFAULT 0
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
