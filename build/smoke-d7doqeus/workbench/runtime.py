from __future__ import annotations
import csv
import io
import json
import math
import os
import socket
import sys
import threading
import time
import webbrowser
from contextlib import suppress
from datetime import date, datetime, timedelta
from pathlib import Path
import psutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from workbench.models import TodoIn, TodoPatch, SettingsPatch, EquipmentPatch
from workbench.diagnostics import (
    configure_logging,
    configure_console,
    install_exception_hooks,
)

configure_console()
import tempfile
from pynput import keyboard, mouse
import uvicorn

try:
    import win32gui
    import win32process
    import winreg
    import win32api
except Exception:
    win32gui = win32process = winreg = win32api = None
try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = ImageDraw = None
try:
    import webview
except Exception:
    webview = None
VERSION = (
    (Path(__file__).resolve().parent.parent / "VERSION.txt")
    .read_text(encoding="utf-8")
    .strip()
)
BASE = Path(__file__).resolve().parent.parent
_SELF_TEST_DIR = (
    tempfile.TemporaryDirectory(prefix="pelican-self-test-")
    if "--self-test" in sys.argv
    else None
)
DATA_DIR = (
    Path(_SELF_TEST_DIR.name)
    if _SELF_TEST_DIR
    else Path(
        os.environ.get(
            "PELICAN_DATA_DIR",
            str(Path(os.environ.get("LOCALAPPDATA", str(BASE))) / "PelicanWorkbench"),
        )
    )
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "pelican.db"
logger = configure_logging(DATA_DIR)
install_exception_hooks(logger)
WEB = BASE / "web"
try:
    from security.runtime_verify import verify_release_integrity
except Exception:
    verify_release_integrity = None
IDLE_SECONDS = 120
TRACK_INTERVAL = 1.0
FOCUS_BREAK_SECONDS = 120
LOCK = threading.RLock()
STOP = threading.Event()
PORT = 0
api = FastAPI(
    title="Pelican Workbench", version=VERSION if "VERSION" in globals() else "3.6"
)
CATEGORY_LABELS = {
    "document": "文档编辑",
    "web": "网页检索",
    "excel": "Excel",
    "ppt": "PPT",
    "wechat": "微信",
    "meeting": "会议",
    "focus": "其他工作",
    "idle": "发呆 / 离开",
}
CATEGORY_ORDER = [
    "document",
    "web",
    "excel",
    "ppt",
    "wechat",
    "meeting",
    "focus",
    "idle",
]
CATEGORY_ICONS = {
    "document": "▤",
    "web": "◌",
    "excel": "▦",
    "ppt": "◫",
    "wechat": "◉",
    "meeting": "◍",
    "focus": "✦",
    "idle": "☾",
}
state = {
    "keys": 0,
    "text_chars": 0,
    "backspace": 0,
    "delete": 0,
    "enter": 0,
    "space": 0,
    "left_click": 0,
    "right_click": 0,
    "middle_click": 0,
    "scroll_events": 0,
    "scroll_distance_px": 0.0,
    "cursor_distance_px": 0.0,
    "activity_events": 0,
    "event_seq": 0,
}
last_xy: tuple[int, int] | None = None
last_monitor_index: tuple[int, int, int, int] | None = None
monitor_layout = []
monitor_layout_signature = ()
monitor_layout_ts = 0.0
last_input_ts = 0.0
listener_refs = []
listener_restart_lock = threading.Lock()
listener_last_ok = 0.0
listener_restart_count = 0
listener_error = ""
tracker_reset_seq = 0
listener_last_keyboard_event = 0.0
listener_last_mouse_event = 0.0
pending_lock = threading.Lock()
pending = {
    "keys": 0,
    "text_chars": 0,
    "backspace": 0,
    "delete_count": 0,
    "enter_count": 0,
    "space_count": 0,
    "left_click": 0,
    "right_click": 0,
    "middle_click": 0,
    "scroll_events": 0,
    "scroll_distance_px": 0.0,
    "cursor_distance_px": 0.0,
    "activity_events": 0,
    "monitor_switches": 0,
}
pending_time = {"active_seconds": 0.0, "idle_seconds": 0.0}
tray_icon = None
webview_window = None
UNLOCK_CATALOG = [
    {
        "item_type": "decoration",
        "item_id": "green_plant",
        "name": "植物",
        "description": "给工作室添一点绿色。",
        "required_level": 1,
    },
    {
        "item_type": "decoration",
        "item_id": "lamp",
        "name": "台灯",
        "description": "温柔的桌面灯光。",
        "required_level": 2,
    },
    {
        "item_type": "decoration",
        "item_id": "coffee_machine",
        "name": "咖啡机",
        "description": "工作室的咖啡补给站。",
        "required_level": 3,
    },
    {
        "item_type": "scene",
        "item_id": "dual_monitor_office",
        "name": "双屏工作室",
        "description": "适配双屏工作的专属布局。",
        "required_level": 4,
    },
    {
        "item_type": "pelican",
        "item_id": "coffee_pelican",
        "name": "咖啡鹈鹕",
        "description": "解锁咖啡主题鹈鹕。",
        "required_level": 5,
    },
    {
        "item_type": "outfit",
        "item_id": "coffee_outfit",
        "name": "咖啡围裙",
        "description": "咖啡主题服装。",
        "required_level": 5,
    },
    {
        "item_type": "decoration",
        "item_id": "fish_tank",
        "name": "鱼缸",
        "description": "工作间的小小水族箱。",
        "required_level": 6,
    },
    {
        "item_type": "accessory",
        "item_id": "headphones",
        "name": "耳机",
        "description": "专注时的工作配饰。",
        "required_level": 7,
    },
    {
        "item_type": "scene",
        "item_id": "sunset_office",
        "name": "黄昏工作室",
        "description": "黄昏时间模式。",
        "required_level": 8,
    },
    {
        "item_type": "effect",
        "item_id": "focus_sparkles",
        "name": "专注星光",
        "description": "专注工作时出现的轻微环境效果。",
        "required_level": 9,
    },
    {
        "item_type": "decoration",
        "item_id": "bookshelf",
        "name": "书架",
        "description": "让工作室更有生活感。",
        "required_level": 10,
    },
]
ACHIEVEMENT_CATALOG = [
    {
        "id": "first_session",
        "name": "第一次 Session",
        "description": "累计有效工作达到 1 分钟。",
        "condition": "active>=60",
        "xp": 25,
    },
    {
        "id": "ten_hours",
        "name": "累计 10 小时",
        "description": "累计有效工作达到 10 小时。",
        "condition": "active>=36000",
        "xp": 100,
    },
    {
        "id": "hundred_hours",
        "name": "累计 100 小时",
        "description": "累计有效工作达到 100 小时。",
        "condition": "active>=360000",
        "xp": 500,
    },
    {
        "id": "multi_monitor",
        "name": "多显示器",
        "description": "检测到至少两块显示器。",
        "condition": "monitors>=2",
        "xp": 50,
    },
    {
        "id": "seven_day_streak",
        "name": "连续 7 天",
        "description": "连续 7 天每天有超过 1 分钟有效工作。",
        "condition": "streak>=7",
        "xp": 100,
    },
]
