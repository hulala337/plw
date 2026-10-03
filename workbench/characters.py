"""Count-only receipts from the journal's opt-in typing area. Never text."""
from typing import Literal
from pydantic import Field, model_validator
from .models import RequestModel


class CharacterReceipt(RequestModel):
    receipt_id: str = Field(pattern=r'^[a-f0-9-]{36}$')
    source: Literal['journal_typing_area']
    day: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    count: int = Field(ge=1, le=10000)
    chinese: int = Field(default=0, ge=0, le=10000)
    english: int = Field(default=0, ge=0, le=10000)
    other: int = Field(default=0, ge=0, le=10000)

    @model_validator(mode='after')
    def validate_totals(self):
        if self.chinese + self.english + self.other != self.count:
            raise ValueError('Character categories must sum to count')
        return self


def receive(connect, receipt):
    from datetime import date
    if receipt.day != date.today().isoformat():
        raise ValueError('Only current-day receipts are accepted')
    conn = connect()
    try:
        with conn:
            conn.execute('INSERT OR IGNORE INTO character_receipts(receipt_id,day,source,count,chinese,english,other) VALUES(?,?,?,?,?,?,?)',
                         (receipt.receipt_id, receipt.day, receipt.source, receipt.count, receipt.chinese, receipt.english, receipt.other))
        return {'ok': True}
    finally:
        conn.close()


def summary(connect, start, end):
    conn = connect()
    try:
        row = conn.execute('SELECT COALESCE(SUM(count),0),COALESCE(SUM(chinese),0),COALESCE(SUM(english),0),COALESCE(SUM(other),0) FROM character_receipts WHERE day BETWEEN ? AND ?', (start, end)).fetchone()
        return {'count': row[0], 'chinese': row[1], 'english': row[2], 'other': row[3], 'unclassified': row[0]-sum(row[1:]), 'unit': 'grapheme_cluster', 'coverage': 'journal_typing_area', 'paste_included': False}
    finally:
        conn.close()
