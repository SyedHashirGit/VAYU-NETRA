import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import ai, engine, optimizer, sim, whatif
from .domain import COMPONENTS
from .store import S

app = FastAPI(title="VAYU-NETRA API", description="Synthetic / simulated data for prototype demonstration.")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _start(): engine.init()


@app.exception_handler(engine.NotFound)
def _nf(_, e): from fastapi.responses import JSONResponse; return JSONResponse({"detail": str(e)}, 404)


def need(aid):
    a = S.get(f"aircraft/{aid}")
    if not a: raise HTTPException(404, f"Aircraft '{aid}' not found")
    return a


@app.get("/api/health")
def health(): return dict(ok=True, store=S.backend, firebase_error=S.fb_error, gemini=bool(os.getenv("GEMINI_API_KEY")), label="Synthetic / simulated data for prototype demonstration.")
@app.get("/api/fleet")
def fleet(): return dict(aircraft=sorted(S.get("aircraft").values(), key=lambda a: a["priority_rank"]))
@app.get("/api/fleet/status")
def fleet_status(): return engine.kpis()
@app.get("/api/aircraft")
def aircraft(): return fleet()
@app.get("/api/aircraft/{aid}")
def aircraft_one(aid: str): return need(aid)
@app.get("/api/aircraft/{aid}/health")
def aircraft_health(aid: str): return dict(aircraft=need(aid), components=S.get(f"predictions/{aid}"))
@app.get("/api/aircraft/{aid}/history")
def history(aid: str):
    need(aid); return dict(records=sorted(S.get(f"maintenance_records/{aid}").values(), key=lambda r: r["hours_ago"]))


@app.get("/api/aircraft/{aid}/components")
def components(aid: str, component: Optional[str] = None):
    """Component list; with ?component= adds telemetry series and a health trend computed by the real model."""
    need(aid); out = []
    for cid, c in S.get(f"components/{aid}").items():
        if component and cid != component: continue
        item = dict(c, prediction=S.get(f"predictions/{aid}/{cid}"), history=[r for r in S.get(f"maintenance_records/{aid}").values() if r["component_id"] == cid],
                    next_action=_next_action(S.get(f"predictions/{aid}/{cid}")))
        if component:
            rd = S.get(f"sensor_readings/{aid}/{cid}"); item["readings"] = rd
            rows = [dict(comp_id=cid, readings=rd[max(0, i - 5):i], n=len(rd), hours_ratio=c["hours_since_overhaul"] / c["overhaul_interval"], prev=c["prev_failures"]) for i in range(5, len(rd) + 1, 2)]
            from .ml import models
            item["health_trend"] = [x["health"] for x in models().predict_many(rows)]
        out.append(item)
    if component and not out: raise HTTPException(404, f"Component '{component}' not found on {aid}")
    return dict(components=out)


def _next_action(p):
    return "Repair / replace now" if p["failure_prob"] >= 0.7 else "Schedule repair within RUL window" if p["failure_prob"] >= 0.4 else "Monitor closely" if p["failure_prob"] >= 0.2 else "Routine monitoring"


@app.get("/api/predictions")
def predictions(): return dict(predictions=[dict(aircraft_id=a, component_id=c, **p) for a, cs in S.get("predictions").items() for c, p in cs.items()])
@app.get("/api/alerts")
def alerts(): return dict(alerts=sorted(S.get("alerts").values(), key=lambda a: (a["acknowledged"], {"critical": 0, "high": 1, "medium": 2}.get(a["severity"], 3))))


@app.post("/api/alerts/ack")
def ack(body: dict):
    a = S.get("alerts").get(body.get("id"))
    if not a: raise HTTPException(404, "Alert not found")
    import datetime; a["acknowledged"] = True; a["ack_at"] = datetime.datetime.now().isoformat(timespec="seconds"); S.commit("alerts"); return a


@app.get("/api/spares")
def spares():
    use = {}
    for a, cs in S.get("predictions").items():
        for c, p in cs.items(): pid = S.get(f"components/{a}/{c}")["part_id"]; use[pid] = use.get(pid, 0) + p["failure_prob"]
    out = []
    for s in S.get("spares").values():
        av = s["stock"] - s["reserved"]; d = round(use.get(s["part_id"], 0), 2)
        out.append(dict(s, available=av, expected_demand=d, shortage_risk="HIGH" if av < 1 or av < d else "MEDIUM" if s["stock"] <= s["min_stock"] else "LOW"))
    return dict(spares=out)


@app.get("/api/technicians")
def technicians(): return dict(technicians=list(S.get("technicians").values()))
@app.get("/api/bays")
def bays(): return dict(bays=list(S.get("bays").values()))


class TelemetryIn(BaseModel):
    aircraft_id: str; component_id: str = "hydraulic_pump"; steps: int = Field(1, ge=1, le=50); rate: float = Field(0.02, ge=0, le=0.2)
@app.post("/api/simulate/telemetry")
def sim_tel(b: TelemetryIn):
    need(b.aircraft_id)
    if b.component_id not in COMPONENTS: raise HTTPException(422, f"Unknown component '{b.component_id}'")
    return sim.step(b.aircraft_id, b.component_id, b.steps, b.rate)


class WhatIfIn(BaseModel):
    aircraft_id: str; component_id: Optional[str] = None; defer_hours: list[int] = [6, 12, 24]
@app.post("/api/simulate/maintenance")
def sim_m(b: WhatIfIn):
    need(b.aircraft_id)
    if any(h <= 0 or h > 96 for h in b.defer_hours): raise HTTPException(422, "defer_hours must be between 1 and 96")
    return whatif.simulate(b.aircraft_id, b.component_id, tuple(b.defer_hours))


@app.post("/api/maintenance/optimize")
def opt():
    try: return optimizer.optimize()
    except optimizer.OptimizerError as e: raise HTTPException(409, str(e))
@app.get("/api/maintenance/plan")
def plan(): return S.get("maintenance_plans/current") or {}
@app.post("/api/maintenance/plan/apply")
def apply():
    try: return optimizer.apply_plan()
    except optimizer.OptimizerError as e: raise HTTPException(409, str(e))


class LogIn(BaseModel): text: str = Field(min_length=10, max_length=4000)
@app.post("/api/maintenance/log/analyze")
def log_analyze(b: LogIn):
    try: return ai.analyze_log(b.text)
    except ValueError as e: raise HTTPException(422, str(e))


class QIn(BaseModel): query: str = Field(min_length=2, max_length=1000)
@app.post("/api/copilot/query")
def copilot(b: QIn): return ai.ask(b.query)


@app.post("/api/admin/reseed")
def reseed(): engine.init(force=True); return dict(ok=True)


FRONT = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "app"
LANDING = Path(__file__).resolve().parents[2] / "landing-page" / "dist"
if FRONT.exists(): app.mount("/app", StaticFiles(directory=FRONT, html=True), name="app")
if LANDING.exists(): app.mount("/", StaticFiles(directory=LANDING, html=True), name="landing")
