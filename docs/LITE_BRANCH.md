# Daily office lightweight branch

- Original main remains unchanged.
- backup/main-working-state-20261003 preserves all pre-existing uncommitted code and artwork.
- feature/daily-office-lite contains the lightweight UI.

The same local database, counters, input listeners, history, tasks and CSV/XLSX exports remain compatible. Do not run both variants simultaneously against the same database.
The UI loads only lite.css, lite-math.js and lite.js. No scene, pet, weather request, equipment or unlock UI is loaded. Legacy compatibility APIs and stored progression records remain available; dashboard polling no longer computes the scene or unlock payload.

Stories use transparent fictional equivalents, never invented actual achievements:
500 estimated input characters/page; 100,000 characters/fictional manuscript;
96 screen pixels/inch for a virtual cursor route; 25 active minutes/record side.
All 16 original summary metrics remain visible in the raw-statistics panel. Range filters affect summaries and export, while replay has an independent date picker.

Validation: Python regression tests, lite DOM/API contract, Node conversion tests,
all JS syntax checks, isolated runtime self-test and actual Edge desktop/mobile
interaction (todo CRUD, date/range controls, replay, no mobile overflow).

Launch: `.venv/Scripts/python.exe app.py`.

## Journal experience

The lightweight journal now includes a category-based daily portrait (excluding
idle time), CSS-only book/path/record artwork, 24 hourly activity bars for the
replay date, and a downloadable local PNG journal card. Card exports include
conversion rules and never contain task titles or recorded text. Empty days
remain empty, with no fabricated progress or productivity ranking.
HTTP calls time out after eight seconds and show recoverable errors. Replay
starts at the first recorded slice and stops at the last. Hidden tabs stop
replay and skip periodic polling. Browser verification covered populated data,
PNG download, mobile overflow and an API failure state in an isolated database.

## Everyday reliability

The date rolls over while the journal remains open; an explicitly selected
historical replay date is preserved. Polling pauses while editing tasks or
mutating data and never interrupts playback. Changing summary ranges disables
card export until matching data arrives, preventing mislabeled exports.

Repeat browser acceptance with `python tools/lite_browser_smoke.py` after
installing Playwright in the QA environment. It uses installed Edge, isolated
SQLite data, no input hooks, and tests literal task text, task completion and
delete, story conversion, PNG download, mobile layout and failed-range export
protection. No browser test data enters the user's actual database.

## Keyboard measurement

Character-key events are counted individually, not inferred from total keyboard
presses. They are NOT committed characters: IME composition, shortcuts, paste,
voice input and edits prevent a global keyboard hook from measuring actual text.
The UI now labels this metric accordingly; historical counters are unchanged.

Daily key TOP5 stores only (day, key position name, count), with no timestamps,
sequence, application association or input text. Auto-repeat is counted. Unknown
positions are grouped as Other. New data begins after the upgrade; old days are
not reconstructed. Clearing today also clears today's key histogram. Schema v2
adds a table and preserves existing data. Older executables that only support
schema v1 will refuse this database; use an independent PELICAN_DATA_DIR if you
need to run the earlier branch.
