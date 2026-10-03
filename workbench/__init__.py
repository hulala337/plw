"""Pelican Workbench application boundaries.

The legacy entry point remains app.py for packaged compatibility; new code can
depend on these small, side-effect-free boundaries without importing the UI.
"""
__all__ = ["database", "tracking", "sessions", "progression", "world", "release"]
