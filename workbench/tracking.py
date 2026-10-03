"""Tracking data contracts, independent of pynput."""
from dataclasses import dataclass

@dataclass(frozen=True)
class InputDelta:
    keys: int = 0
    text_chars: int = 0
    cursor_distance_px: float = 0.0
    scroll_events: int = 0
