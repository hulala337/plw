from pathlib import Path
import json, importlib.util
ROOT=Path(__file__).resolve().parent
for p in (ROOT/"data").glob("*.json"):
    json.loads(p.read_text(encoding="utf-8"))
print("JSON validation: PASS")
spec=importlib.util.spec_from_file_location("server",ROOT/"app"/"server.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("FastAPI import: PASS")
print("Version:",m.health()["version"],"Events:",m.health()["events"])
print("Simulation choices:",len(m.sim["event_choices"]))
