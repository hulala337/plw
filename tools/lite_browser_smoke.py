"""Optional Edge browser acceptance; uses temporary data and no live hooks.

Install playwright in a separate QA environment with runtime dependencies.
Run from the repository root: python tools/lite_browser_smoke.py
"""
import logging
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="journal-browser-") as data:
        os.environ["PELICAN_DATA_DIR"] = data
        from workbench import routes, runtime, database, services, application

        database.init_db()
        services.seed_progression_catalog()
        database.ensure_today()
        day = services.today_key()
        conn = database.db()
        conn.execute("UPDATE daily SET text_chars=12500,active_seconds=7200 WHERE day=?", (day,))
        conn.execute("INSERT INTO app_usage VALUES(?,?,?)", (day, "document", 7200))
        conn.execute("INSERT INTO activity_slices VALUES(?,?,?,?)", (day + "T09:00", "document", 60, 20))
        conn.commit()
        conn.close()
        application.run_server()
        try:
            assert application.wait_for_server()
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge", headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{runtime.PORT}")
                page.wait_for_selector(".story")
                assert "25" in page.locator(".story strong").first.inner_text()
                assert page.locator(".pulse-column").count() == 24
                page.check("#characterOptIn")
                page.locator("#characterPad").press_sequentially("abc")
                page.wait_for_function("document.querySelector('.character-tile.total strong').textContent==='3'")
                page.evaluate("""() => {
                    const p=document.getElementById('characterPad');
                    p.dispatchEvent(new CompositionEvent('compositionstart'));
                    p.value += '\u4f60\u597d';
                    p.dispatchEvent(new InputEvent('input',{inputType:'insertCompositionText',data:'\u4f60\u597d',isComposing:true}));
                    p.dispatchEvent(new CompositionEvent('compositionend',{data:'\u4f60\u597d'}));
                }""")
                page.wait_for_function("document.querySelector('.character-tile.total strong').textContent==='5'")
                page.evaluate("""() => {
                    const p=document.getElementById('characterPad');
                    p.dispatchEvent(new InputEvent('beforeinput',{inputType:'insertFromPaste',data:'ignored'}));
                    p.value += 'ignored';
                    p.dispatchEvent(new InputEvent('input',{inputType:'insertFromPaste',data:'ignored'}));
                }""")
                page.wait_for_timeout(200)
                assert page.locator('.character-tile.total strong').inner_text() == '5'
                assert page.locator('.character-tile.chinese strong').inner_text() == '2'
                assert page.locator('.character-tile.english strong').inner_text() == '3'
                page.fill("#todoTitle", "<b>literal task</b>")
                page.click("#todoForm button")
                page.wait_for_selector(".todo")
                assert page.locator(".todo b").count() == 0
                page.check(".todo input")
                page.wait_for_selector(".todo.done")
                page.click(".todo button")
                page.wait_for_selector(".todo", state="detached")
                with page.expect_download() as download:
                    page.click("#saveCard")
                path = Path(data) / "journal.png"
                download.value.save_as(path)
                assert path.read_bytes().startswith(b"\x89PNG")
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                # Keep snapshots optional and out of the tracked source tree.
                if os.getenv("JOURNAL_SCREENSHOT"):
                    page.screenshot(path=os.environ["JOURNAL_SCREENSHOT"], full_page=True)
                page.route("**/api/dashboard?*", lambda route: route.fulfill(status=503, body="{}"))
                page.select_option("#range", "week")
                page.wait_for_function("document.getElementById('message').textContent.includes('503')")
                assert page.locator("#saveCard").is_disabled()
                assert not errors, errors
                browser.close()
            print("Browser acceptance: PASS (stories, tasks, PNG, mobile, error recovery guard)")
        finally:
            application.shutdown_runtime()
            logging.shutdown()


if __name__ == "__main__":
    main()
