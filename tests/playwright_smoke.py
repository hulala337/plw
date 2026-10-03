"""Optional browser smoke test. Uses installed Edge when Chromium is unavailable."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    page = browser.new_page()
    page.goto((root / "web" / "index.html").as_uri())
    page.wait_for_timeout(500)
    assert page.locator('[data-view="growth"]').count() == 1
    assert page.locator('#view-growth').count() == 1
    page.locator('[data-view="growth"]').click()
    assert page.locator('#view-growth').is_visible()
    browser.close()
