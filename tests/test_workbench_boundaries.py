from datetime import datetime, timedelta
from workbench.progression import level_for_xp
from workbench.sessions import SessionWindow
from workbench.world import DisplayRect

def test_progression_is_deterministic():
    assert level_for_xp(0) == 1
    assert level_for_xp(600) == 2
    assert level_for_xp(999999) == 12

def test_session_duration():
    start = datetime.now() - timedelta(seconds=10)
    assert SessionWindow(start).duration_seconds >= 9

def test_negative_monitor_coordinates():
    assert DisplayRect(-1920, -100, 0, 980).size == (1920, 1080)
