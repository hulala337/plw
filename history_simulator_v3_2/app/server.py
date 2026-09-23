from pathlib import Path
import json
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEB = ROOT / "app" / "web"
ASSETS = ROOT / "assets"

def load(name):
    path = DATA / name
    if not path.is_file():
        raise RuntimeError(f"Missing data file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

timeline = load("canonical_timeline_v3_2.json")
facts = load("fact_check_matrix_v3_2.json")
sources = load("source_registry_v3_2.json")
boundary = load("information_boundary_v3_2.json")
integrity = load("model_integrity_rules_v3_2.json")
map_registry = load("may_fourth_map_registry_v3_2.json")
sim = load("simulation_rules_v3_2.json")
context = load("historical_context_v3_2.json")
visuals = load("node_visuals_v3_2.json")

app = FastAPI(title="如果我是他们 V3.2", version="3.2.0")
app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")

@app.get("/")
def index():
    return FileResponse(WEB / "index.html")

@app.get("/health")
def health():
    return {
        "ok": True,
        "version": "3.2.0",
        "events": len(timeline["events"]),
        "features": ["historical-boundary", "fact-check", "source-traceability", "multi-actor", "teacher-cockpit", "may-fourth-map"],
    }

@app.get("/api/scenario")
def scenario():
    return timeline

@app.get("/api/fact-check")
def fact_check():
    return facts

@app.get("/api/source-registry")
def source_registry():
    return sources

@app.get("/api/information-boundary")
def information_boundary():
    return boundary

@app.get("/api/integrity-rules")
def integrity_rules():
    return integrity

@app.get("/api/map/may-fourth")
def may_fourth():
    return map_registry

@app.get("/api/event/{event_id}")
def event(event_id: str):
    ev = next((x for x in timeline["events"] if x["id"] == event_id), None)
    if ev is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    fact = next((x for x in facts["events"] if x["id"] == event_id), None)
    linked_sources = [
        s for s in sources["sources"]
        if event_id in s.get("covers", [])
    ]
    return {"event": ev, "fact_check": fact, "sources": linked_sources}

@app.get("/api/historical-context")
def historical_context():
    return context

@app.get("/api/node-visuals")
def node_visuals():
    return visuals

@app.get("/api/simulation-rules")
def simulation_rules():
    return {
        "version": sim["version"],
        "state_initial": sim["state_initial"],
        "state_labels": sim["state_labels"],
        "actors": sim["actors"],
        "event_choices": sim["event_choices"],
    }

def clamp(v):
    return max(0, min(100, int(v)))

@app.post("/api/simulate")
def simulate(payload: dict = Body(...)):
    event_id = payload.get("event_id")
    choice_id = payload.get("choice_id")
    state = dict(payload.get("state") or sim["state_initial"])

    if event_id not in sim["event_choices"]:
        raise HTTPException(status_code=404, detail="event_not_found")
    picked = next((c for c in sim["event_choices"][event_id] if c["id"] == choice_id), None)
    if picked is None:
        raise HTTPException(status_code=400, detail="choice_not_found")

    for key in sim["state_initial"]:
        state[key] = clamp(state.get(key, sim["state_initial"][key]))
    before = dict(state)

    for key, value in picked["effects"].items():
        state[key] = clamp(state.get(key, 50) + value)

    # Simulation feedback only; these are not historical facts.
    friction = max(0, (state["resistance"] - state["political"]) // 8)
    state["stability"] = clamp(state["stability"] - friction)
    if state["foreign_pressure"] > 65:
        state["finance"] = clamp(state["finance"] - 3)
    if state["education"] > 55 and state["mobilization"] > 45:
        state["nationalism"] = clamp(state["nationalism"] + 2)
    if state["nationalism"] > 65:
        state["resistance"] = clamp(state["resistance"] + 2)

    delta = {k: state[k] - before[k] for k in state if state[k] != before[k]}
    actor_response = []
    ctx = next((x for x in context["events"] if x["id"] == event_id), None)
    if ctx:
        for actor in ctx["actors"]:
            actor_response.append({
                "actor": actor["actor"],
                "stance": actor["stance"],
                "response": f"选择“{picked['text']}”后，需要重新权衡其既有立场、资源和政治利益。",
                "direction": "contextual"
            })
    if state["resistance"] > 60:
        actor_response.append({"actor": "系统反馈", "stance": "模拟机制", "response": "制度/社会阻力较高，执行成本增加。", "direction": "negative"})
    if state["mobilization"] > 55:
        actor_response.append({"actor": "系统反馈", "stance": "模拟机制", "response": "社会动员较高，参与扩大但协调成本也增加。", "direction": "mixed"})
    if state["foreign_pressure"] > 60:
        actor_response.append({"actor": "系统反馈", "stance": "模拟机制", "response": "外部压力较高，财政与外交空间承压。", "direction": "negative"})

    return {
        "event_id": event_id,
        "choice_id": choice_id,
        "choice_text": picked["text"],
        "before": before,
        "after": state,
        "delta": delta,
        "effects_authored": picked["effects"],
        "actor_response": actor_response,
        "interpretation": [
            "这是模拟反馈，不是历史事实。",
            "结果由本次选择、既有状态、系统反馈共同产生，不把结果倒推为选择时的必然答案。",
        ],
    }

@app.get("/api/version")
def version():
    return {"version": "3.2.0", "codename": "史实与史料校准层"}
