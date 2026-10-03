"""Release validation helpers."""
from pathlib import Path

def required_files(root: Path) -> list[Path]:
    return [root / "app.py", root / "VERSION.txt", root / "web" / "index.html", root / "web" / "assets" / "app.js"]
