"""Gemini 2.5 Flash layer. Numbers always come from backend tools. If Gemini is unavailable the
local deterministic fallback (clearly labelled) answers using the SAME tools."""
import os, re, json, functools
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from .domain import COMPONENTS
from .engine import S, NotFound, kpis, refresh
from . import whatif, optimizer

MODEL = "gemini-3.8-flash"


def _err(e): return {"error": str(e)}


# ---------------- backend tools (exposed to Gemini via function calling) ----------------
def get_fleet_status() -> dict:
    """Fleet KPIs: availability, counts by status, alerts, spare and capacity summary."""
    return kpis()

def get_aircraft_health(aircraft_id: str) -> dict:
    """Health, risk, RUL, impact and per-component predictions for one aircraft (e.g. 'A17')."""
    a = S.get(f"aircraft/{aircraft_id}")
    if not a: return _err(f"Aircraft '{aircraft_id}' not found")
    return dict(aircraft=a, components={c: dict(health=p["health"], failure_prob=p["failure_prob"], rul=[p["rul_low"], p["rul_high"]], impact=p["impact"]["score"]) for c, p in S.get(f"predictions/{aircraft_id}").items()})

def get_component_health(aircraft_id: str, component_id: str) -> dict:
    """Full prediction (probability, RUL range, anomaly, risk drivers, impact) for one component, e.g. hydraulic_pump."""
    p = S.get(f"predictions/{aircraft_id}/{component_id}")
    return p if p else _err(f"No prediction for {aircraft_id}/{component_id}")

def get_aircraft_history(aircraft_id: str) -> dict:
    """Maintenance history records for an aircraft."""
    r = S.get(f"maintenance_records/{aircraft_id}")
    return dict(records=sorted(r.values(), key=lambda x: x["hours_ago"])) if r is not None else _err(f"Aircraft '{aircraft_id}' not found")

def get_fleet_impact(top_n: int = 8) -> dict:
    """Aircraft ranked by fleet impact score (transparent formula), highest first."""
    ac = sorted(S.get("aircraft").values(), key=lambda a: a["priority_rank"])[:top_n]
    return dict(ranking=[dict(rank=a["priority_rank"], aircraft=a["id"], impact_score=a["impact_score"], level=a["impact_level"], component=a["top_impact_component"], failure_risk=a["failure_risk"],
                              health=a["health"], status=a["status"], rul=[a["rul_low"], a["rul_high"]]) for a in ac],
                formula=next(iter(S.get(f"predictions/{ac[0]['id']}").values()))["impact"]["formula"])

def get_spare_inventory() -> dict:
    """Spare parts with stock, reserved, available, lead time; flags parts with shortage."""
    sp = [dict(s, available=s["stock"] - s["reserved"], shortage=(s["stock"] - s["reserved"]) < 1) for s in S.get("spares").values()]
    return dict(shortages=[s for s in sp if s["shortage"]], low_stock=[s for s in sp if not s["shortage"] and s["stock"] <= s["min_stock"]], total_parts=len(sp))

def get_technician_availability() -> dict:
    """Technicians with skills and hours until free."""
    return dict(technicians=list(S.get("technicians").values()))

def get_bay_availability() -> dict:
    """Maintenance bays with supported types and hours until free."""
    return dict(bays=list(S.get("bays").values()))

def simulate_maintenance(aircraft_id: str, action: str = "compare", duration: int = 12) -> dict:
    """What-if comparison for the aircraft's highest-risk component. action: 'repair_now', 'defer' or 'bundle' (or 'compare' for all). duration: deferral hours."""
    try: r = whatif.simulate(aircraft_id, None, (6, 12, 24, duration) if duration not in (6, 12, 24) else (6, 12, 24))
    except NotFound as e: return _err(e)
    r["requested_action"] = action; r["requested_duration_h"] = duration
    return r

def optimize_maintenance_schedule() -> dict:
    """Run the OR-Tools optimizer now and return the schedule with before/after metrics."""
    try: return _slim(optimizer.optimize())
    except optimizer.OptimizerError as e: return _err(e)

def get_maintenance_plan() -> dict:
    """Return the most recent optimized maintenance plan (runs optimizer if none exists)."""
    p = S.get("maintenance_plans/current")
    return _slim(p) if p else optimize_maintenance_schedule()

def _slim(p): return {k: v for k, v in p.items() if k != "label"}

TOOLS = [get_fleet_status, get_aircraft_health, get_component_health, get_aircraft_history, get_fleet_impact, get_spare_inventory, get_technician_availability,
         get_bay_availability, simulate_maintenance, optimize_maintenance_schedule, get_maintenance_plan]
SYSTEM = ("You are VAYU-NETRA Copilot for a predictive-maintenance prototype using SYNTHETIC data. NEVER state any number (probability, RUL, downtime, availability) "
          "that did not come from a tool result. Always call the relevant tool first, then explain concisely, including WHY. Do not claim real military data or validated accuracy. "
          "Recommend actions as decision support only.")


def _gemini_ask(q, calls):
    from google import genai
    from google.genai import types
    def wrap(fn):
        @functools.wraps(fn)
        def w(*a, **k):
            try: out = fn(*a, **k)
            except Exception as e: out = _err(e)
            calls.append(dict(name=fn.__name__, args=k or list(a), ok="error" not in out)); return out
        return w
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r = client.models.generate_content(model=MODEL, contents=q, config=types.GenerateContentConfig(system_instruction=SYSTEM, tools=[wrap(f) for f in TOOLS], temperature=0.2))
    if not r.text: raise RuntimeError("empty Gemini response")
    return r.text


# ---------------- local deterministic fallback ----------------
def _fallback(q, calls):
    ql = q.lower(); m = re.search(r"\bA\s?(\d{1,2})\b", q, re.I); aid = f"A{int(m.group(1)):02d}" if m else None
    hrs = re.search(r"(\d+)\s*(?:h|hr|hour)", ql); dur = int(hrs.group(1)) if hrs else 12
    def call(fn, *a, **k):
        out = fn(*a, **k); calls.append(dict(name=fn.__name__, args=k or list(a), ok="error" not in out)); return out
    if any(w in ql for w in ("delay", "defer", "what if", "what happens", "simulate", "bundle", "repair now")) and aid:
        r = call(simulate_maintenance, aid, "compare", dur)
        if "error" in r: return r["error"]
        rows = "\n".join(f"- {s['name']}: expected downtime {s['expected_downtime_h']} h, failure risk {s['failure_risk']*100:.0f}%, fleet availability {s['fleet_availability_pct']}%" for s in r["scenarios"])
        return f"What-if for {aid} {r['component']}:\n{rows}\nRecommended: {next(s for s in r['scenarios'] if s['best'])['name']}.\n" + "\n".join(r["why"])
    if any(w in ql for w in ("optimiz", "optimis", "schedule", "plan", "chose")):
        p = call(get_maintenance_plan)
        if "error" in p: return p["error"]
        top = p["schedule"][:4]
        s = "; ".join(f"{r['aircraft']} {r['task']} on {r['technician']}/{r['bay']} at +{r['start']}h ({r['reason']})" for r in top)
        return (f"Optimizer ({p['status']}): projected availability {p['before']['projected_availability_pct']}% -> {p['after']['projected_availability_pct']}% (+{p['availability_gain_pts']} pts). First tasks: {s}. "
                + " ".join(p["notes"]))
    if "spare" in ql or "shortage" in ql or "inventory" in ql:
        r = call(get_spare_inventory)
        return "Spare shortages: " + (", ".join(f"{s['part_id']} (available {s['available']}, lead {s['lead_time_h']} h)" for s in r["shortages"]) or "none") + ". Low stock: " + (", ".join(s["part_id"] for s in r["low_stock"]) or "none") + "."
    if aid and ("why" in ql or "health" in ql or "risk" in ql or "priorit" in ql):
        a = call(get_aircraft_health, aid)
        if "error" in a: return a["error"]
        ac = a["aircraft"]; c = call(get_component_health, aid, ac["top_impact_component"])
        dr = ", ".join(f"{d['label']} +{d['pct']}%" for d in c["drivers"])
        return (f"{aid} is rank #{ac['priority_rank']} (impact {ac['impact_score']}/100, {ac['impact_level']}). Worst component {ac['top_impact_component']}: failure probability {c['failure_prob']*100:.0f}%, "
                f"RUL {c['rul_low']}-{c['rul_high']} h, health {c['health']}. Risk drivers: {dr}. Downtime if repaired {c['impact']['expected_downtime_h']} h"
                f"{', spare short' if c['impact']['spare_short'] else ''}.")
    if any(w in ql for w in ("prioritiz", "priority", "highest", "impact", "today", "first")):
        r = call(get_fleet_impact, 5)
        return "Top fleet impact: " + "; ".join(f"#{x['rank']} {x['aircraft']} ({x['component']}, impact {x['impact_score']}, risk {x['failure_risk']*100:.0f}%)" for x in r["ranking"]) + f". Formula: {r['formula']}"
    k = call(get_fleet_status)
    return f"Fleet availability {k['fleet_availability_pct']}%: {k['ready']} ready, {k['degraded']} degraded, {k['critical']} critical, {k['maintenance']} in maintenance. {k['critical_alerts']} unacknowledged high/critical alerts."


def ask(q):
    calls = []
    if os.getenv("GEMINI_API_KEY"):
        try: return dict(answer=_gemini_ask(q, calls), tool_calls=calls, engine=MODEL)
        except Exception as e:
            calls.clear(); note = f"Gemini unavailable ({type(e).__name__}); answered by local deterministic fallback using the same backend tools."
    else: note = "GEMINI_API_KEY not set; answered by local deterministic fallback using the same backend tools."
    return dict(answer=_fallback(q, calls), tool_calls=calls, engine="local-fallback", note=note)


# ---------------- maintenance-log extraction ----------------
class LogExtraction(BaseModel):
    aircraft_id: str = Field(pattern=r"^A\d{2}$")
    component: Literal["engine", "hydraulic_pump", "valve", "avionics", "landing_gear", "fuel_pump"]
    fault: str = Field(min_length=2, max_length=80)
    severity: Literal["low", "medium", "high"]
    previous_replacements: int = Field(ge=0, le=50, default=0)
    operating_hours: Optional[int] = Field(default=None, ge=0)
    recurring_fault: bool = False


def _regex_extract(t):
    tl = t.lower(); m = re.search(r"\bA\s?(\d{1,2})\b", t); comp = next((c for c, kws in {"hydraulic_pump": ["hydraulic pump", "hydraulic"], "valve": ["valve"], "engine": ["engine"], "avionics": ["avionic"],
                                                                                           "landing_gear": ["landing"], "fuel_pump": ["fuel"]}.items() if any(k in tl for k in kws)), None)
    nums = {"once": 1, "twice": 2, "thrice": 3}; rep = re.search(r"replaced\s+(\w+)\s+times?|replaced\s+(once|twice|thrice)|(\d+)\s+(?:previous\s+)?replacements?", tl)
    n = 0
    if rep:
        g = next(x for x in rep.groups() if x); n = int(g) if g.isdigit() else nums.get(g, 0)
    hrs = re.search(r"(\d+)\s*(?:operating\s*)?(?:hours|hrs|h)\b", tl)
    fault = "pressure_fluctuation" if "pressure" in tl and "fluct" in tl else "overtemperature" if "overheat" in tl or "temperature" in tl else "vibration" if "vibrat" in tl else "leak" if "leak" in tl else "unspecified_fault"
    sev = "high" if any(w in tl for w in ("critical", "severe", "failure", "failed")) else "low" if any(w in tl for w in ("minor", "cosmetic")) else "medium"
    return dict(aircraft_id=f"A{int(m.group(1)):02d}" if m else "", component=comp or "", fault=fault, severity=sev, previous_replacements=n,
                operating_hours=int(hrs.group(1)) if hrs else None, recurring_fault=bool(n >= 1 or "recurr" in tl or "intermittent" in tl or "again" in tl))


def analyze_log(text, extractor=None):
    """Extract -> validate (Pydantic) -> store -> re-run predictions. Raises ValueError with a meaningful message."""
    engine, raw = "local-regex", None
    if extractor is None and os.getenv("GEMINI_API_KEY"):
        try:
            from google import genai
            from google.genai import types
            r = genai.Client(api_key=os.environ["GEMINI_API_KEY"]).models.generate_content(model=MODEL, contents="Extract the maintenance record from this note:\n" + text,
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=LogExtraction, temperature=0))
            raw, engine = json.loads(r.text), MODEL
        except Exception: raw = None
    if raw is None: raw = (extractor or _regex_extract)(text)
    try: rec = LogExtraction.model_validate(raw)
    except ValidationError as e: raise ValueError("Could not extract a valid record (check the note names an aircraft like A17 and a known component): " + "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()))
    if not S.get(f"aircraft/{rec.aircraft_id}"): raise ValueError(f"Aircraft {rec.aircraft_id} does not exist in the fleet")
    recs = S.data["maintenance_records"][rec.aircraft_id]; rid = f"R{len(recs)+1:03d}-L{sum(len(v) for v in S.get('maintenance_records').values())}"
    recs[rid] = dict(id=rid, aircraft_id=rec.aircraft_id, component_id=rec.component, hours_ago=0, type="log", fault=rec.fault, note=text[:400], source=engine, extracted=rec.model_dump())
    comp = S.data["components"][rec.aircraft_id][rec.component]
    comp["prev_failures"] = max(comp["prev_failures"], rec.previous_replacements)
    S.commit(f"maintenance_records/{rec.aircraft_id}", f"components/{rec.aircraft_id}/{rec.component}")
    refresh({rec.aircraft_id})
    return dict(record=rec.model_dump(), stored_as=rid, engine=engine, prediction=S.get(f"predictions/{rec.aircraft_id}/{rec.component}"))
