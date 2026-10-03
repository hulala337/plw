from __future__ import annotations

from . import runtime


def enforce_release_integrity() -> None:
    is_bundled = bool(
        getattr(runtime.sys, "frozen", False) or globals().get("__compiled__", False)
    )
    if not is_bundled:
        return
    if runtime.verify_release_integrity is None:
        reason = "完整性校验模块不可用"
    else:
        ok, reason = runtime.verify_release_integrity(runtime.BASE)
        if ok:
            return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0,
            f"鹈鹕工作台启动被阻止。\n\n{reason}\n\n请从正版渠道重新安装。",
            "鹈鹕工作台 · 完整性保护",
            16,
        )
    except Exception:
        pass
    raise SystemExit(f"Pelican Workbench integrity check failed: {reason}")


def shutdown_runtime() -> None:
    for listener in list(runtime.listener_refs):
        with runtime.suppress(Exception):
            listener.stop()
    runtime.listener_refs.clear()
    runtime.STOP.set()
    for thread in runtime.threading.enumerate():
        if thread.name == "tracker":
            thread.join(timeout=10)
    if hasattr(runtime, "http_server"):
        runtime.http_server.should_exit = True
        runtime.http_thread.join(timeout=10)


def run_server() -> int:
    sock = runtime.socket.socket()
    sock.bind(("127.0.0.1", 0))
    runtime.PORT = sock.getsockname()[1]
    runtime.http_server = runtime.uvicorn.Server(
        runtime.uvicorn.Config(
            runtime.api, host="127.0.0.1", port=runtime.PORT, log_level="warning"
        )
    )
    runtime.http_thread = runtime.threading.Thread(
        target=runtime.http_server.run,
        kwargs={"sockets": [sock]},
        daemon=True,
        name="http-server",
    )
    runtime.http_thread.start()
    return runtime.PORT


def wait_for_server(timeout: float = 5.0) -> bool:
    import urllib.request
    import urllib.error
    deadline = runtime.time.monotonic() + timeout
    while runtime.time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{runtime.PORT}/api/health", timeout=0.5) as response:
                response.read()
                return response.status == 200
        except (OSError, urllib.error.URLError):
            runtime.time.sleep(0.05)
    return False


def main() -> None:
    from . import application, database, desktop, selftest, services, tracking

    application.enforce_release_integrity()
    if "--self-test" in runtime.sys.argv:
        raise SystemExit(selftest.self_test())
    database.init_db()
    services.seed_progression_catalog()
    database.recover_stale_sessions()
    database.ensure_today()
    desktop.set_windows_dpi_awareness()
    application.run_server()
    if not application.wait_for_server():
        raise SystemExit("Pelican Workbench local server failed to start")
    if not tracking.listeners_start():
        pass
    runtime.threading.Thread(
        target=tracking.tracker, daemon=True, name="tracker"
    ).start()
    runtime.threading.Thread(
        target=tracking.listener_watchdog, daemon=True, name="listener-watchdog"
    ).start()
    if "--tray" in runtime.sys.argv:
        desktop.start_tray()
    elif runtime.os.name == "nt" and runtime.pystray:
        tray_thread = runtime.threading.Thread(
            target=desktop.start_tray, daemon=True, name="tray"
        )
        tray_thread.start()
        ui_owned_loop = desktop.open_ui()
        if ui_owned_loop:
            runtime.STOP.set()
        else:
            while not runtime.STOP.wait(0.5):
                pass
    else:
        ui_owned_loop = desktop.open_ui()
        if ui_owned_loop:
            runtime.STOP.set()
        else:
            while not runtime.STOP.wait(0.5):
                pass
