import sqlite3
import unittest
from pydantic import ValidationError
from workbench.migrations import migrate
from workbench.models import TodoIn, SettingsPatch


class InfrastructureTests(unittest.TestCase):
    def test_legacy_upgrade_preserves_data_and_is_repeatable(self):
        with sqlite3.connect(":memory:") as conn:
            conn.executescript("""
                CREATE TABLE daily(day TEXT PRIMARY KEY);
                CREATE TABLE todos(id INTEGER PRIMARY KEY);
                CREATE TABLE activity_slices(slice_start TEXT PRIMARY KEY, category TEXT, seconds INTEGER, events INTEGER);
                INSERT INTO activity_slices VALUES('2026-10-01T10:00','web',30,2);
            """)
            migrate(conn)
            migrate(conn)
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertEqual(
                conn.execute("SELECT seconds FROM activity_slices").fetchone()[0], 30
            )
            conn.execute(
                "INSERT INTO activity_slices VALUES('2026-10-01T10:00','document',15,1)"
            )
            self.assertIn(
                "completion_count",
                [r[1] for r in conn.execute("PRAGMA table_info(todos)")],
            )

    def test_failed_upgrade_rolls_back(self):
        with sqlite3.connect(":memory:") as conn:
            conn.executescript("CREATE TABLE daily(day TEXT);")
            with self.assertRaises(sqlite3.OperationalError):
                migrate(conn)
            self.assertEqual(
                [r[1] for r in conn.execute("PRAGMA table_info(daily)")], ["day"]
            )
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)

    def test_future_database_rejected(self):
        with sqlite3.connect(":memory:") as conn:
            conn.execute("PRAGMA user_version=4")
            with self.assertRaises(RuntimeError):
                migrate(conn)

    def test_request_limits(self):
        for value in ("", "   ", "x" * 501):
            with self.assertRaises(ValidationError):
                TodoIn(title=value)
        with self.assertRaises(ValidationError):
            SettingsPatch(idle_seconds=901)
        self.assertEqual(SettingsPatch(idle_seconds=120).idle_seconds, 120)


class RequestContractTests(unittest.TestCase):
    def test_unknown_fields_and_coerced_values_rejected(self):
        from workbench.models import SettingsPatch, TodoPatch, EquipmentPatch
        for factory, payload in (
            (SettingsPatch, {"idle_seconds": "120"}),
            (SettingsPatch, {"unknown": True}),
            (TodoPatch, {"done": "false"}),
            (EquipmentPatch, {"slot": "scene", "item_id": "x" * 129}),
        ):
            with self.assertRaises(ValidationError):
                factory(**payload)

    def test_unicode_title_roundtrip(self):
        title = "\u9e48\u9e55 \U0001f426"
        model = TodoIn(title="  " + title + "  ")
        self.assertEqual(TodoIn.model_validate_json(model.model_dump_json()).title, title)
