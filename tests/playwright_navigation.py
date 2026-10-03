from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=edge)
    page = browser.new_page()
    page.goto((root / "web/index.html").as_uri())
    for view in ("home", "replay", "timeline", "stats", "growth", "settings"):
        page.locator(f'[data-view="{view}"]').click()
        assert page.locator(f"#view-{view}").is_visible(), view
    browser.close()
