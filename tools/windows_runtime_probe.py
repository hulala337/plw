"""Record available Windows input/display capabilities for acceptance evidence."""
import json, platform
result = {"platform": platform.platform(), "monitors": []}
try:
    import win32api
    for handle, hdc, rect in win32api.EnumDisplayMonitors():
        left, top, right, bottom = map(int, rect)
        result["monitors"].append({"left": left, "top": top, "right": right, "bottom": bottom, "width": right-left, "height": bottom-top})
except Exception as exc:
    result["display_error"] = str(exc)
try:
    import ctypes
    result["dpi_awareness_set"] = bool(ctypes.windll.user32.SetProcessDPIAware())
except Exception as exc:
    result["dpi_error"] = str(exc)
try:
    from pynput import keyboard, mouse
    k, m = keyboard.Listener(on_press=lambda key: None), mouse.Listener(on_move=lambda x,y: None)
    k.start(); m.start(); result["keyboard_hook"] = k.is_alive(); result["mouse_hook"] = m.is_alive(); k.stop(); m.stop()
except Exception as exc:
    result["hook_error"] = str(exc)
print(json.dumps(result, ensure_ascii=False, indent=2))
