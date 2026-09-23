from __future__ import annotations

import json
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "art-work" / "generated"
APPROVED = ROOT / "art-work" / "approved"
REJECTED = ROOT / "art-work" / "rejected"
REVIEWS = ROOT / "art-work" / "reviews"

for d in [APPROVED, REJECTED, REVIEWS]:
    d.mkdir(parents=True, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def send_html(self, body: str, status=200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            cards = []
            for p in sorted(CANDIDATES.glob("*.png")):
                cards.append(
                    f'<article><h2>{p.stem}</h2>'
                    f'<img src="/image/{p.name}">'
                    f'<p><a href="/review?action=approve&asset={p.name}">APPROVE</a> '
                    f'<a href="/review?action=reject&asset={p.name}">REJECT</a></p></article>'
                )
            html = """<!doctype html><meta charset="utf-8"><title>Pelican Art Review</title>
<style>body{font-family:system-ui;margin:24px;background:#f6f5f1}article{display:inline-block;vertical-align:top;width:440px;margin:12px;padding:16px;background:white;border-radius:16px;box-shadow:0 2px 12px #0001}img{max-width:100%;height:320px;object-fit:contain;background:#eee}a{display:inline-block;margin-right:16px;padding:8px 12px;border-radius:8px;background:#eee;text-decoration:none;color:#222}</style>""" + "".join(cards)
            self.send_html(html)
            return

        if parsed.path.startswith("/image/"):
            path = CANDIDATES / Path(parsed.path.removeprefix("/image/")).name
            if not path.exists():
                self.send_error(404)
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/review":
            q = parse_qs(parsed.query)
            action = q.get("action", [""])[0]
            asset = Path(q.get("asset", [""])[0]).name
            src = CANDIDATES / asset
            if action not in {"approve", "reject"} or not src.exists():
                self.send_error(400)
                return

            target_dir = APPROVED if action == "approve" else REJECTED
            shutil.copy2(src, target_dir / asset)
            review = {"asset": src.stem, "action": action}
            (REVIEWS / f"{src.stem}.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
            self.send_html(f"<meta http-equiv='refresh' content='0;url=/'><p>{action}: {src.stem}</p>")
            return

        self.send_error(404)


def main():
    print("Review server: http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()


if __name__ == "__main__":
    main()
