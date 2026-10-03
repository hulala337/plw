# Fixed office edition

Branch: backup/main-working-state-20261003. Original branch snapshot is preserved
in commit ca4efd1. The lightweight branch and main are unchanged.

The office uses one daylight background, one monitor composition and one working
pelican illustration. Time/weather/state directors are not loaded; no geolocation
or weather requests run. The real clock and collection health remain live.
Growth navigation, equipment controls, weather and pet toggles are removed.
Legacy progression tables and internal compatibility endpoints remain for data
compatibility, but no upgrades are presented or used to select the scene.

Layout: the home page owns the scene, overview, tasks and timeline. Statistics
owns category distribution, trend, export and input details. Duplicate home
trend/summary/distribution and scene todo board are hidden. The right rail starts
beside the scene instead of below it. No rhythm score is displayed.

Input details include mouse left/right/middle clicks and total, scroll events
and driver units (historical scroll_distance_px / 120; not rotations or physical
length), daily key TOP5, and separate confirmed Chinese/English/other characters.
Character capture only covers the opt-in textarea, not other applications; paste
is excluded. Global character-key events remain separate. Cursor stays in pixels;
physical metres are not claimed. Schema v4 is compatible with the current lite
branch but older schema-v1 executables require an independent data directory.

Verification: 11 regression tests, frontend contract and JS checks, actual HTTP
self-test and headless Edge checks for fixed scene, navigation, character input
and absence of weather requests. Real desktop/IME/multi-monitor acceptance is
still separate from simulated browser input.
