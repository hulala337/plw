"""Daily key-position histograms, never ordered events or input text."""
from collections import Counter
from datetime import date
from threading import RLock

lock = RLock()
pending = Counter()


def key_label(key):
    vk = getattr(key, 'vk', None)
    if vk is None:
        vk = getattr(getattr(key, 'value', None), 'vk', None)
    names = {8:'Backspace',9:'Tab',13:'Enter',16:'Shift',17:'Ctrl',18:'Alt',
             20:'CapsLock',27:'Esc',32:'Space',33:'PageUp',34:'PageDown',
             35:'End',36:'Home',37:'Left',38:'Up',39:'Right',40:'Down',46:'Delete',
             160:'LeftShift',161:'RightShift',162:'LeftCtrl',163:'RightCtrl',
             164:'LeftAlt',165:'RightAlt',91:'LeftWin',92:'RightWin',
             186:';',187:'=',188:',',189:'-',190:'.',191:'/',192:'`',
             219:'[',220:'\\',221:']',222:"'",106:'Numpad*',107:'Numpad+',109:'Numpad-',110:'Numpad.',111:'Numpad/'}
    if vk in names:
        return names[vk]
    if isinstance(vk, int):
        if 48 <= vk <= 57 or 65 <= vk <= 90:
            return chr(vk)
        if 96 <= vk <= 105:
            return f'Numpad{vk-96}'
        if 112 <= vk <= 135:
            return f'F{vk-111}'
    return 'Other'


def record(key, day=None):
    with lock:
        pending[(day or date.today().isoformat(), key_label(key))] += 1


def flush(connect):
    with lock:
        if not pending:
            return
        conn = connect()
        try:
            with conn:
                conn.executemany('INSERT INTO daily_key_counts(day,key_name,count) VALUES(?,?,?) '
                    'ON CONFLICT(day,key_name) DO UPDATE SET count=count+excluded.count',
                    [(day,key,count) for (day,key),count in pending.items()])
            pending.clear()
        finally:
            conn.close()


def top(connect, day):
    flush(connect)
    conn = connect()
    try:
        rows = conn.execute('SELECT key_name,count FROM daily_key_counts WHERE day=? ORDER BY count DESC,key_name LIMIT 5',(day,)).fetchall()
        total = conn.execute('SELECT COALESCE(SUM(count),0) FROM daily_key_counts WHERE day=?',(day,)).fetchone()[0]
        return {'day':day,'total':total,'keys':[dict(r) for r in rows]}
    finally:
        conn.close()
