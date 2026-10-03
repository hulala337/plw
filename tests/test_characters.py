import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from pydantic import ValidationError
from workbench.characters import CharacterReceipt, receive, summary


class CharactersTests(unittest.TestCase):
    def test_counts_retry_and_legacy(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'counts.db'
            def connect():
                return sqlite3.connect(path)
            conn = connect()
            conn.execute('CREATE TABLE character_receipts(receipt_id TEXT PRIMARY KEY,day TEXT,source TEXT,count INTEGER,chinese INTEGER,english INTEGER,other INTEGER)')
            today = date.today().isoformat()
            conn.execute('INSERT INTO character_receipts VALUES(?,?,?,?,?,?,?)',('legacy',today,'journal_typing_area',7,0,0,0))
            conn.commit()
            conn.close()
            receipt = CharacterReceipt(receipt_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',source='journal_typing_area',day=today,count=6,chinese=2,english=3,other=1)
            receive(connect, receipt)
            receive(connect, receipt)
            result = summary(connect,today,today)
            self.assertEqual((result['count'],result['chinese'],result['english'],result['other'],result['unclassified']),(13,2,3,1,7))

    def test_inconsistent_counts_rejected(self):
        with self.assertRaises(ValidationError):
            CharacterReceipt(receipt_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',source='journal_typing_area',day=date.today().isoformat(),count=5,chinese=2,english=2,other=0)
