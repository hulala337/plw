from pathlib import Path
import json
import importlib.util

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

json_files = sorted(DATA.glob("*.json"))
for p in json_files:
    json.loads(p.read_text(encoding="utf-8"))
print(f"JSON validation: PASS ({len(json_files)} files)")

spec = importlib.util.spec_from_file_location("history_server", ROOT / "app" / "server.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("FastAPI import: PASS")

assert module.health()["version"] == "3.2.0"
assert module.health()["events"] == 22
assert len(module.timeline["events"]) == 22
assert len(module.context["events"]) == 22
assert all(len(x["actors"]) == 3 for x in module.context["events"])
assert len(module.visuals["items"]) >= 4

rules = module.sim
assert set(rules["state_initial"]) == set(rules["state_labels"])
assert len(rules["event_choices"]) == 22
for event in module.timeline["events"]:
    eid = event["id"]
    choices = rules["event_choices"].get(eid)
    assert choices and len(choices) == 3, f"{eid}: expected 3 choices"
    assert {c["id"] for c in choices} == {"A", "B", "C"}
    for choice in choices:
        assert isinstance(choice["text"], str) and choice["text"]
        assert all(k in rules["state_initial"] for k in choice["effects"])

# Exercise every simulation branch once.
for event in module.timeline["events"]:
    for choice in module.sim["event_choices"][event["id"]]:
        result = module.simulate({"event_id": event["id"], "choice_id": choice["id"], "state": module.sim["state_initial"]})
        assert len(result["after"]) == len(module.sim["state_initial"])
        assert all(0 <= v <= 100 for v in result["after"].values())

assert (ROOT / "assets" / "maps" / "may_fourth_1919_spatial_map.svg").is_file()
print("Simulation validation: PASS (22 events × 3 choices)")
assert any(x["id"] == "e18" and x["type"] == "reconstruction_map" for x in module.visuals["items"])
print("Historical context: PASS (22 events × 3 actor perspectives)")
print("Embedded visual registry: PASS")
print("May Fourth map: PASS")
print("V3.2 validation: PASS")
