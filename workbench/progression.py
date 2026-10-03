"""Pure progression calculations used by Growth tests."""
def level_for_xp(xp: int, max_level: int = 12) -> int:
    return min(max_level, 1 + max(0, int(xp)) // 600)
