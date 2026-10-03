import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from workbench import key_counts


class KeyCountsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.db'
        key_counts.pending.clear()
        conn = self.connect()
        conn.execute('CREATE TABLE daily_key_counts(day TEXT,key_name TEXT,count INTEGER,PRIMARY KEY(day,key_name))')
        conn.commit()
        conn.close()

    def tearDown(self):
        key_counts.pending.clear()
        self.temp.cleanup()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def test_daily_top_five_and_no_event_content(self):
        for vk in range(65, 72):
            for _ in range(vk - 64):
                key_counts.record(SimpleNamespace(vk=vk, char='ignored'), '2026-10-03')
        key_counts.record(SimpleNamespace(vk=65), '2026-10-04')
        result = key_counts.top(self.connect, '2026-10-03')
        self.assertEqual(result['total'], 28)
        self.assertEqual([r['key_name'] for r in result['keys']], ['G','F','E','D','C'])
        self.assertEqual(key_counts.top(self.connect,'2026-10-04')['total'],1)
        self.assertEqual(key_counts.top(self.connect,'2026-10-03'),result)

    def test_failure_retains_pending(self):
        key_counts.record(SimpleNamespace(vk=13), '2026-10-03')
        def fail():
            raise sqlite3.OperationalError('unavailable')
        with self.assertRaises(sqlite3.OperationalError):
            key_counts.flush(fail)
        self.assertEqual(key_counts.top(self.connect,'2026-10-03')['keys'],[{'key_name':'Enter','count':1}])

    def test_unknown_and_modifier_mapping(self):
        self.assertEqual(key_counts.key_label(SimpleNamespace(char='secret')), 'Other')
        self.assertEqual(key_counts.key_label(SimpleNamespace(value=SimpleNamespace(vk=160))), 'LeftShift')
