from __future__ import annotations

from . import runtime


def startup_enabled() -> bool:
    if not runtime.winreg:
        return False
    with runtime.suppress(Exception):
        key = runtime.winreg.OpenKey(
            runtime.winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            0,
            runtime.winreg.KEY_READ,
        )
        val, _ = runtime.winreg.QueryValueEx(key, "PelicanWorkbench")
        runtime.winreg.CloseKey(key)
        return bool(val)
    return False


def app_launch_command() -> str:
    exe = runtime.Path(runtime.sys.executable)
    script = runtime.Path(__file__).resolve()
    if exe.name.lower().startswith("python"):
        return f'"{exe}" "{script}" --tray'
    return f'"{exe}" --tray'


def set_startup(enabled: bool) -> bool:
    from . import desktop

    if not runtime.winreg:
        return False
    key = runtime.winreg.CreateKey(
        runtime.winreg.HKEY_CURRENT_USER,
        "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
    )
    if enabled:
        runtime.winreg.SetValueEx(
            key,
            "PelicanWorkbench",
            0,
            runtime.winreg.REG_SZ,
            desktop.app_launch_command(),
        )
    else:
        with runtime.suppress(FileNotFoundError):
            runtime.winreg.DeleteValue(key, "PelicanWorkbench")
    runtime.winreg.CloseKey(key)
    return desktop.startup_enabled()


def make_tray_image():
    if runtime.Image is None:
        return None
    im = runtime.Image.new("RGBA", (64, 64), (24, 43, 63, 255))
    d = runtime.ImageDraw.Draw(im)
    d.ellipse((8, 10, 48, 53), fill=(248, 248, 241), outline=(117, 157, 179), width=2)
    d.polygon([(34, 27), (60, 34), (36, 43)], fill=(241, 155, 31))
    d.ellipse((25, 20, 29, 24), fill=(28, 44, 54))
    d.arc((12, 28, 38, 53), 20, 140, fill=(206, 218, 224), width=3)
    return im


def open_ui() -> bool:
    url = f"http://127.0.0.1:{runtime.PORT}/"
    if runtime.webview:
        if runtime.webview_window:
            with runtime.suppress(Exception):
                runtime.webview_window.show()
                runtime.webview_window.restore()
                runtime.webview_window.bring_to_front()
            return
        try:
            runtime.webview_window = runtime.webview.create_window(
                "鹈鹕工作台",
                url,
                width=1520,
                height=960,
                min_size=(1120, 720),
                background_color="#eef4f8",
            )

            def on_closing():
                if runtime.STOP.is_set():
                    return True
                with runtime.suppress(Exception):
                    runtime.webview_window.hide()
                return False

            runtime.webview_window.events.closing += on_closing
            runtime.webview.start(gui="edgechromium", debug=False)
            return True
        except Exception:
            with runtime.suppress(Exception):
                runtime.webbrowser.open(url)
            return False
    runtime.webbrowser.open(url)
    return False


def start_tray() -> None:
    from . import desktop

    "Run the Windows tray icon loop.\n\n    pywebview's GUI loop must stay on the main thread on Windows, so the\n    tray loop is deliberately hosted in a background thread for normal UI\n    launches.  The tray-only startup path still uses this function directly.\n    "
    if not runtime.pystray:
        return

    def quit_app(icon, item):
        runtime.STOP.set()
        with runtime.suppress(Exception):
            if runtime.webview_window:
                runtime.webview_window.destroy()
        with runtime.suppress(Exception):
            icon.stop()

    def show_app(icon, item):
        if runtime.webview_window:
            with runtime.suppress(Exception):
                runtime.webview_window.show()
                runtime.webview_window.restore()
                runtime.webview_window.bring_to_front()
        else:
            runtime.threading.Thread(
                target=desktop.open_ui, daemon=True, name="ui-request"
            ).start()

    menu = runtime.pystray.Menu(
        runtime.pystray.MenuItem("打开鹈鹕工作台", show_app, default=True),
        runtime.pystray.MenuItem(
            "开机启动",
            lambda icon, item: desktop.set_startup(not desktop.startup_enabled()),
        ),
        runtime.pystray.MenuItem("退出程序", quit_app),
    )
    runtime.tray_icon = runtime.pystray.Icon(
        "PelicanWorkbench", desktop.make_tray_image(), "鹈鹕工作台", menu
    )
    runtime.tray_icon.run()


def set_windows_dpi_awareness() -> None:
    """Keep pynput and Win32 monitor coordinates in the same physical-pixel space."""
    if runtime.os.name != "nt":
        return
    with runtime.suppress(Exception):
        import ctypes

        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
            return
    with runtime.suppress(Exception):
        import ctypes

        ctypes.windll.user32.SetProcessDPIAware()


def display_info() -> dict:
    from . import tracking

    monitors = []
    if runtime.win32api is not None:
        try:
            for m in tracking.refresh_monitor_layout(force=True):
                monitors.append(dict(m))
        except Exception:
            monitors = []
    if not monitors and runtime.os.name == "nt":
        with runtime.suppress(Exception):
            import ctypes

            user32 = ctypes.windll.user32
            monitors = [
                {
                    "name": "PRIMARY",
                    "left": 0,
                    "top": 0,
                    "right": user32.GetSystemMetrics(0),
                    "bottom": user32.GetSystemMetrics(1),
                    "width": user32.GetSystemMetrics(0),
                    "height": user32.GetSystemMetrics(1),
                }
            ]
    current = None
    if runtime.last_xy is not None:
        current = tracking.monitor_at(runtime.last_xy[0], runtime.last_xy[1])
    current_index = None
    if current is not None:
        for m in monitors:
            if (m["left"], m["top"], m["right"], m["bottom"]) == current:
                current_index = m["index"]
                break
    return {
        "count": len(monitors),
        "mode": "single" if len(monitors) <= 1 else "multi",
        "monitors": monitors,
        "current_monitor_index": current_index,
        "current_cursor": {"x": runtime.last_xy[0], "y": runtime.last_xy[1]}
        if runtime.last_xy is not None
        else None,
    }
