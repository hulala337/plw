# P0 Acceptance Test Matrix

Acceptance rule: a P0 case passes only when the complete chain works: Windows input -> Tracker -> SQLite -> API -> frontend -> visible state. Static inspection is not enough for input behavior.

## A. Tracker -> SQLite

| ID | Scenario | Action | Expected |
|---|---|---|---|
| P0-T01 | Keyboard | Press 10 ordinary keys | daily.keys +10; printable keys also increase text_chars |
| P0-T02 | Special keys | Backspace/Delete/Enter/Space | matching counters increase |
| P0-T03 | Mouse move | Move pointer | cursor_distance_px increases in Euclidean pixels |
| P0-T04 | Mouse click | Left/right/middle click | matching counters increase |
| P0-T05 | Scroll | Scroll up/down | scroll_events and scroll distance increase |
| P0-T06 | Activity | Mixed input | activity_events increases |
| P0-T07 | Atomic persistence | Generate input while tracker runs | daily + timeline + app usage commit consistently |
| P0-T08 | DB failure | Temporarily lock/unavailable DB | tracker stays alive; queued input is not silently discarded |
| P0-T09 | Idle | Stop input beyond threshold | active time stops; idle time increases |
| P0-T10 | Session | Work then idle past break threshold | session closes with end time/reason |
| P0-T11 | Restart recovery | Restart after an open session | stale session is recovered |
| P0-T12 | Forget today | Delete today's data | daily/timeline/app/session data is cleared and counters reset |

## B. Multi-monitor

| ID | Scenario | Expected |
|---|---|---|
| P0-M01 | Single monitor | API count=1 and mode=single |
| P0-M02 | Multiple monitors | API returns actual count and monitor rectangles |
| P0-M03 | Cross-screen movement | continuous virtual-desktop pixel distance; monitor switch counted |
| P0-M04 | Negative coordinates | displays left/above primary work correctly |
| P0-M05 | Topology change | attach/detach/rearrange refreshes cached layout |

## C. API contract

| ID | Endpoint | Expected |
|---|---|---|
| P0-A01 | GET / | HTML loads |
| P0-A02 | GET /api/health | listener/tracker/database status |
| P0-A03 | GET /api/dashboard?range=today | summary/timeline/sessions/todos/display |
| P0-A04 | GET /api/dashboard?range=week | week data changes |
| P0-A05 | GET /api/dashboard?range=month | month data changes |
| P0-A06 | GET /api/display-info | monitor layout |
| P0-A07 | GET /api/settings | persisted settings |
| P0-A08 | PATCH /api/settings | change survives GET |
| P0-A09 | POST /api/todos | creates item and ID |
| P0-A10 | PATCH /api/todos/{id} | completion persists |
| P0-A11 | DELETE /api/todos/{id} | item disappears |
| P0-A12 | GET /api/replay | replay source returned |
| P0-A13 | POST /api/forget-today | reset completes |
| P0-A14 | GET /api/export/csv | UTF-8 CSV generated |
| P0-A15 | GET /api/export/xlsx | XLSX generated |

## D. Frontend navigation and interaction

| ID | Scenario | Expected |
|---|---|---|
| P0-U01 | Startup | Today visible with no JS startup exception |
| P0-U02 | Main nav | Today/Replay/Timeline/Stats/Growth/Settings each opens its view |
| P0-U03 | Secondary jump | rail Data/Privacy/Theme/About actions open Settings |
| P0-U04 | Timeline controls | Now, zoom +/- and scrubber respond |
| P0-U05 | Stats tabs | Today/Week/Month change active tab and refresh data |
| P0-U06 | Replay | Start Replay advances through events |
| P0-U07 | Settings | toggles/select persist after reload |
| P0-U08 | Todo create | submit creates and renders item |
| P0-U09 | Todo complete | check moves item to DONE and persists |
| P0-U10 | Todo delete | delete removes item and persists |
| P0-U11 | Empty state | empty data never breaks navigation |
| P0-U12 | Reload | persisted state remains consistent |

## E. Evidence required for final P0 acceptance

1. /api/health result
2. /api/display-info result
3. keyboard before/after counters
4. mouse before/after pixel distance
5. corresponding SQLite rows
6. screenshots/video of primary navigation
7. Todo create -> complete -> delete
8. Stats range switching
9. Replay playback
10. Settings change -> restart -> persisted value
11. Self-test output
12. packaged EXE launch evidence

Current repository code has a static/self-test foundation, but Windows runtime evidence is still required before P0 can be declared accepted.
