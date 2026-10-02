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
