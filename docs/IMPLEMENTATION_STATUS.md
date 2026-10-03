# Implementation status

The project keeps `app.py` as the packaged compatibility entry point. New
side-effect-free boundaries live under `workbench/` for database policy,
tracking contracts, sessions, progression, world geometry, and release checks.

Automated gates run Python compilation, preflight asset hashing, unit tests,
JavaScript syntax validation, and the P0/P1 contract checks in CI.

Windows-only acceptance remains required for global input hooks, IME behavior,
real monitor topology/DPI, WebView interaction, and installer launch.
