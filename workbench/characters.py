"""Count-only receipts from the journal's opt-in typing area. Never text."""
from typing import Literal
from pydantic import Field
from .models import RequestModel


class CharacterReceipt(RequestModel):
    receipt_id: str = Field(pattern=r'^[a-f0-9-]{36}$')
    source: Literal['journal_typing_area']
    day: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    count: int = Field(ge=1, le=10000)


def receive(connect, receipt):
    from datetime import date
    if receipt.day != date.today().isoformat():
        raise ValueError('Only current-day receipts are accepted')
    conn = connect()
    try:
        with conn:
            conn.execute('INSERT OR IGNORE INTO character_receipts(receipt_id,day,source,count) VALUES(?,?,?,?)',
                         (receipt.receipt_id, receipt.day, receipt.source, receipt.count))
        return {'ok': True}
    finally:
        conn.close()


def summary(connect, start, end):
    conn = connect()
    try:
        count = conn.execute('SELECT COALESCE(SUM(count),0) FROM character_receipts WHERE day BETWEEN ? AND ?', (start, end)).fetchone()[0]
        return {'count': count, 'unit': 'grapheme_cluster', 'coverage': 'journal_typing_area', 'paste_included': False}
    finally:
        conn.close()
