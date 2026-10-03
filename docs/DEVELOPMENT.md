# Development and release checks

Supported baseline: Windows x64 / Python 3.11. All lock files include transitive
versions. They are platform-specific and should be regenerated in a clean venv.

## Environments

| Setup argument | Environment | Lock |
| --- | --- | --- |
| app | .venv | requirements-lock-windows.txt |
| build | .venv | requirements-build-lock-windows.txt |
| pipeline | .venv-pipeline | art-pipeline/requirements-lock-windows.txt |
| mcp | .venv-mcp | tools/xingai_mcp/requirements-lock-windows.txt |

Run `./tools/setup.ps1 -Environment all` to install and validate all three.
The build environment is a superset of the desktop runtime; AI SDKs never enter
the desktop dependency lock. Tool checks are offline and do not generate media.
Node.js 22 must be on PATH (or `.tools/node.exe`) for strict release checks.

## Modules

`app.py` only registers routes and starts/stops the application.
`workbench/database.py` owns persistence helpers, `schema.py` the base schema,
`migrations.py` transactional upgrades, `tracking.py` listeners and counters,
`services.py` scoring/progression/world projection, `routes.py` HTTP handlers,
`desktop.py` tray/window/Windows integration, `application.py` service lifecycle,
`selftest.py` isolated runtime verification. `runtime.py` is the explicit shared
process context: locks, counters, configuration and platform handles. Modules
access this context directly so mutable values cannot become stale imports.
Models, error handlers and diagnostics are independent modules.

## Verification

- `python tools/check_project.py --require-node`: UTF-8/static reference checks,
  dependency consistency, Python compilation, migration/request tests, frontend
  contract checks, every frontend JS syntax check and actual HTTP/hook self-test.
- `python tools/build_smoke.py`: isolated staging copy, disposable test key,
  signature verification, real PyInstaller build and packaged self-test.
  Output is test-signed and must not be distributed as an official release.
- `build_release.bat`: pinned build dependencies and strict preflight, followed
  by production signing/build/installer steps. It does not rewrite source.

Runtime tests use temporary data and do not touch the user's real database.
Normal data lives in LOCALAPPDATA/PelicanWorkbench or PELICAN_DATA_DIR.
Logs rotate at 1 MB with three backups. Error responses retain `detail`, adding
`code`; unexpected failures return a correlation ID, not internal exception text.
Validation errors omit submitted input. Source files use UTF-8; console and
release subprocesses explicitly use UTF-8. `.editorconfig` and `.gitattributes`
record encoding/line-ending conventions. API JSON preserves Unicode.

All shipped web resources are signed. The donation image defaults to the
existing placeholder; supplying a real QR image is a separate content task.
Physical multi-monitor checks, UI interaction and installation/uninstallation
remain human acceptance checks; an automated smoke test cannot certify them.
