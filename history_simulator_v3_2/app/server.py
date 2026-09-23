from pathlib import Path
import json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
WEB=ROOT/"app"/"web"
ASSETS=ROOT/"assets"

def load(name):
    return json.loads((DATA/name).read_text(encoding="utf-8"))

timeline=load("canonical_timeline_v3_2.json")
facts=load("fact_check_matrix_v3_2.json")
sources=load("source_registry_v3_2.json")
boundary=load("information_boundary_v3_2.json")
rules=load("model_integrity_rules_v3_2.json")
map_registry=load("may_fourth_map_registry_v3_2.json")

app=FastAPI(title="如果我是他们 V3.2",version="3.2.0")
app.mount("/assets",StaticFiles(directory=ASSETS),name="assets")

@app.get("/")
def index(): return FileResponse(WEB/"index.html")
@app.get("/health")
def health(): return {"ok":True,"version":"3.2.0","events":len(timeline["events"]),"features":["historical-boundary","fact-check","source-traceability","multi-actor","teacher-cockpit","may-fourth-map"]}
@app.get("/api/scenario")
def scenario(): return timeline
@app.get("/api/fact-check")
def fact_check(): return facts
@app.get("/api/source-registry")
def source_registry(): return sources
@app.get("/api/information-boundary")
def information_boundary(): return boundary
@app.get("/api/integrity-rules")
def integrity_rules(): return rules
@app.get("/api/map/may-fourth")
def may_fourth(): return map_registry
@app.get("/api/event/{event_id}")
def event(event_id:str):
    ev=next((x for x in timeline["events"] if x["id"]==event_id),None)
    if not ev: return {"error":"event_not_found"}
    fact=next((x for x in facts["events"] if x["event_id"]==event_id),None)
    return {"event":ev,"fact_check":fact,"sources":[s for s in sources["sources"] if event_id in s.get("events",[])]}
@app.get("/api/version")
def version(): return {"version":"3.2.0","codename":"史实与史料校准层"}
