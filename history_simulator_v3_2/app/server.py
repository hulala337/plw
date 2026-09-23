from pathlib import Path
import json
from fastapi import FastAPI, Body
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
sim=load("simulation_rules_v3_2.json")

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

@app.get("/api/simulation-rules")
def simulation_rules(): return {"version":sim["version"],"state_initial":sim["state_initial"],"state_labels":sim["state_labels"],"actors":sim["actors"]}

@app.post("/api/simulate")
def simulate(payload: dict = Body(...)):
    event_id=payload.get("event_id"); choice_id=payload.get("choice_id"); state=dict(payload.get("state") or sim["state_initial"])
    choices=sim["event_choices"].get(event_id,[])
    picked=next((c for c in choices if c[0]==choice_id),None)
    if not picked: return {"error":"choice_not_found","event_id":event_id}
    effects=picked[2]; before=dict(state)
    for k,v in effects.items(): state[k]=max(0,min(100,state.get(k,50)+v))
    # authored system feedback: interactions, delayed costs, and path dependence
    friction=max(0,(state.get("resistance",0)-state.get("political",0))//8)
    state["stability"]=max(0,min(100,state["stability"]-friction))
    if state["foreign_pressure"]>65: state["finance"]=max(0,state["finance"]-3)
    if state["education"]>55 and state["mobilization"]>45: state["nationalism"]=min(100,state["nationalism"]+2)
    if state["nationalism"]>65: state["resistance"]=min(100,state["resistance"]+2)
    delta={k:state[k]-before.get(k,0) for k in state if state[k]!=before.get(k,0)}
    actor_response=[]
    if state["resistance"]>60: actor_response.append({"actor":"守旧势力","response":"阻力上升，执行成本增加","direction":"negative"})
    if state["mobilization"]>55: actor_response.append({"actor":"士绅、商人、工人和民众","response":"社会参与扩大，但协调成本增加","direction":"mixed"})
    if state["education"]>50: actor_response.append({"actor":"新式知识青年","response":"新式知识与公共讨论空间扩大","direction":"positive"})
    if state["political"]>55: actor_response.append({"actor":"清廷中枢","response":"制度整合能力发生变化，地方关系需要重新协调","direction":"mixed"})
    if state["foreign_pressure"]>60: actor_response.append({"actor":"列强与国际力量","response":"外部约束持续，财政与外交空间承压","direction":"negative"})
    return {"event_id":event_id,"choice_id":choice_id,"choice_text":picked[1],"before":before,"after":state,"delta":delta,"effects_authored":effects,"actor_response":actor_response,"interpretation":["这是模拟反馈，不是历史事实。","结果由本次选择、既有状态、系统反馈共同产生，不把结果倒推为选择时的必然答案。"]}
\n@app.get("/api/version")
def version(): return {"version":"3.2.0","codename":"史实与史料校准层"}
