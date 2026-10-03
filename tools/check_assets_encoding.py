"""Validate UTF-8 source and local static references without network access."""
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".py", ".js", ".css", ".html", ".md", ".json", ".toml", ".txt", ".yml", ".yaml", ".ps1", ".bat", ".svg", ".iss", ".spec"}

def main():
    tracked = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    errors = []
    for rel in tracked:
        p = ROOT / rel
        if p.suffix.lower() not in TEXT or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8-sig")
        except UnicodeError:
            errors.append(rel + ": invalid UTF-8")
            continue
        if "\ufffd" in text or re.search(r"[\ue000-\uf8ff]", text):
            errors.append(rel + ": suspicious replacement/private-use character")
    for p in (ROOT / "web").rglob("*"):
        if p.suffix not in {".html", ".css", ".svg"}:
            continue
        text = p.read_text(encoding="utf-8")
        refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', text)
        refs += re.findall(r'url\(["\']?([^"\')]+)', text)
        for ref in refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc or not url.path or "${" in ref:
                continue
            path = unquote(url.path)
            target = ROOT / "web" / path.lstrip("/") if path.startswith("/") else p.parent / path
            if not target.is_file():
                errors.append(f"{p.relative_to(ROOT)}: missing {ref}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("UTF-8 and local static references: PASS")

if __name__ == "__main__":
    main()
