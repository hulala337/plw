# P2 Acceptance Matrix — World / Art / Product Experience

P2 covers the part of Pelican Workbench that turns reliable work data into a coherent living work world. P2 is not accepted by screenshots alone; the selected state must be driven by real application data.

## A. World state

| ID | Scenario | Expected |
|---|---|---|
| P2-W01 | Active Session | World/Pelican exposes working state |
| P2-W02 | Idle beyond threshold | World/Pelican changes to resting/idle state |
| P2-W03 | Long active period | Tired/fatigue state can be selected without changing identity |
| P2-W04 | Multi-monitor | Eligible unlocked scene adapts to actual monitor count |
| P2-W05 | Equipped scene | Selected scene persists after restart |
| P2-W06 | Equipped pelican/outfit | Selected identity persists after restart |
| P2-W07 | Multiple decorations | Decorations coexist and do not overwrite each other |
| P2-W08 | Locked item | Cannot be equipped |
| P2-W09 | Unknown item | API rejects it without corrupting equipment |
| P2-W10 | Refresh/restart | World projection remains consistent with Growth/Equipment |

## B. Growth

| ID | Scenario | Expected |
|---|---|---|
| P2-G01 | Active time | XP increases according to active time only |
| P2-G02 | Idle time | No time XP awarded |
| P2-G03 | Todo completion | One XP reward per completion event |
| P2-G04 | Achievement | One reward per achievement |
| P2-G05 | Refresh/restart | No duplicate reward |
| P2-G06 | Level-up | Eligible unlocks become available |
| P2-G07 | Forget Today | Daily statistics are removed; lifetime growth remains |
| P2-G08 | Fresh database | Default scene/pelican/outfit are available |

## C. Art consistency

Every P0/P1 character or scene candidate must pass:

- B01 identity consistency
- body/head/bill/eye proportion consistency
- clothing consistency
- office spatial consistency
- palette and lighting consistency
- no malformed limbs
- no random text/AI artifacts
- no third-party character/logo copying
- correct transparent/background treatment according to Manifest

A visual QA PASS only moves an asset to human review. It does not approve it.

## D. Animation

- Working animation is driven by working state.
- Thinking animation is driven by thinking state.
- Coffee interaction preserves cup/wing contact.
- Eye micro-animation does not alter character identity.
- prefers-reduced-motion disables non-essential motion.
- Animation failure cannot break navigation or data refresh.

## E. Product visual regression

Verify:
- main navigation remains clickable
- decorative layers never intercept controls
- scene and UI layers maintain intended z-index
- TODO remains real DOM data, not baked into an illustration
- Timeline/Stats/Replay remain data-driven
- empty states remain navigable
- visual assets can be replaced without changing Tracker/API behavior

## F. Release / packaging

Before a release is declared complete:

1. build succeeds from main
2. installer is produced
3. fresh install launches
4. Tracker receives real input
5. SQLite persists data
6. main navigation works
7. Growth payload loads
8. world projection loads
9. Self Test passes
10. resource integrity check passes
11. uninstall/reinstall does not expose secrets or private keys

## G. Evidence

P2 acceptance should retain:

- representative screenshots
- world-state API payload
- Growth payload
- equipment payload
- Self Test output
- visual regression result
- selected approved asset IDs
- build/installer verification

P2 is complete only when the evidence is reproducible from GitHub main.
