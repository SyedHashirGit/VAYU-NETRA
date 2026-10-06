"""OR-Tools CP-SAT maintenance scheduler. Hours are integer offsets from 'now'."""
import math, datetime as dt
from ortools.sat.python import cp_model
from .domain import COMPONENTS, HORIZON_H, risk_before, unplanned_penalty
from .engine import S, spare_avail, spare_lead, waits
from .whatif import BUNDLE_FACTOR, fleet_base_downtime

H = 120


class OptimizerError(Exception): pass


def build_tasks(bundle=True):
    tasks, sched = [], {t["aircraft"]: dict(t) for t in S.get("maintenance_tasks").values() if t["status"] == "scheduled"}
    used = set()
    preds = [(a, c, p) for a, cs in S.get("predictions").items() for c, p in cs.items() if p["failure_prob"] >= 0.30 and S.get(f"aircraft/{a}")["status"] != "MAINTENANCE"]
    for aid, cid, p in sorted(preds, key=lambda x: -x[2]["impact"]["score"]):
        m, comp = COMPONENTS[cid], S.get(f"components/{aid}/{cid}")
        prio = {1: 1.5, 2: 1.15, 3: 1.0}[S.get(f"aircraft/{aid}")["op_priority"]]
        s = sched.get(aid)
        t = dict(id=f"PM-{aid}-{cid}", aircraft=aid, component=cid, label=f"{m['label']} repair", kind="predictive", dur=m["repair"], skill=m["skill"], bay=m["bay"],
                 part=comp["part_id"], release=0, flex=H, p=p["failure_prob"], repair=m["repair"], deadline=int(p["rul_low"]), weight=1 + round(20 * p["failure_prob"] * m["crit"] * prio))
        if bundle and s and s["id"] not in used and _bundle_pays_off(p, m, comp, s):
            used.add(s["id"])
            t.update(id=s["id"], kind="bundled", label=f"Scheduled inspection + {m['label']} repair", dur=s["duration"] + math.ceil(BUNDLE_FACTOR * m["repair"]),
                     release=s["window_start"], flex=24)
        tasks.append(t)
    for aid, s in sched.items():
        if s["id"] in used: continue
        tasks.append(dict(id=s["id"], aircraft=aid, component="inspection", label=s["label"], kind="scheduled", dur=s["duration"], skill="general", bay="general", part=None,
                          release=s["window_start"], flex=24, p=0.0, repair=0, deadline=s["window_start"] + 24, weight=2))
    return tasks


def _bundle_pays_off(p, m, comp, s):
    """Bundle only if expected downtime (incl. risk until the window) beats a standalone repair."""
    try: tw, bw = waits(m["skill"], m["bay"])
    except Exception: return False  # no qualified resource: cannot bundle; task is reported as unschedulable
    lead = 0 if spare_avail(comp["part_id"]) >= 1 else spare_lead(comp["part_id"])
    pen = unplanned_penalty(m["repair"]); start = max(tw, bw, lead)
    alone = m["repair"] + risk_before(p["failure_prob"], start) * pen
    bundled = math.ceil(BUNDLE_FACTOR * m["repair"]) + risk_before(p["failure_prob"], max(s["window_start"], lead)) * pen
    return bundled < alone


def _evaluate(rows, tasks):
    by = {t["id"]: t for t in tasks}
    down = fleet_base_downtime() - sum(x["duration"] for x in S.get("maintenance_tasks").values() if x["status"] == "scheduled") + sum(r["end"] - r["start"] for r in rows)
    unplanned = sum(risk_before(by[r["task_id"]]["p"], r["start"]) * unplanned_penalty(by[r["task_id"]]["repair"]) for r in rows if by[r["task_id"]]["p"] > 0)
    n = len(S.get("aircraft"))
    return dict(planned_downtime_h=round(down, 1), expected_unplanned_downtime_h=round(unplanned, 1),
                projected_availability_pct=round(100 * (1 - (down + unplanned) / (n * HORIZON_H)), 2),
                avg_risk_before_start_pct=round(100 * sum(risk_before(by[r["task_id"]]["p"], r["start"]) for r in rows if by[r["task_id"]]["p"] > 0) / max(1, sum(1 for r in rows if by[r["task_id"]]["p"] > 0)), 1))


def baseline(tasks):
    """FIFO baseline: tasks in aircraft-ID order, earliest qualified resources, no risk ordering, no bundling."""
    tech = {k: v["free_at"] for k, v in S.get("technicians").items()}; bay = {k: v["free_at"] for k, v in S.get("bays").items()}
    left = {k: spare_avail(k) for k in S.get("spares")}; rows = []
    for t in sorted(tasks, key=lambda x: x["aircraft"]):
        ts = [k for k, v in S.get("technicians").items() if t["skill"] in v["skills"]]; bs = [k for k, v in S.get("bays").items() if t["bay"] in v["supports"]]
        if not ts or not bs: continue
        a, b = min(ts, key=lambda k: tech[k]), min(bs, key=lambda k: bay[k])
        lead = 0
        if t["part"]:
            if left[t["part"]] > 0: left[t["part"]] -= 1
            else: lead = spare_lead(t["part"])
        st = max(t["release"], tech[a], bay[b], lead); tech[a] = bay[b] = st + t["dur"]
        rows.append(dict(task_id=t["id"], start=st, end=st + t["dur"]))
    return rows


def optimize(apply_persist=True):
    tasks = build_tasks(True)
    techs, bays = S.get("technicians"), S.get("bays")
    unsched, ok = [], []
    for t in tasks:
        if not any(t["skill"] in v["skills"] for v in techs.values()): unsched.append(dict(task_id=t["id"], reason=f"no technician with skill '{t['skill']}'"))
        elif not any(t["bay"] in v["supports"] for v in bays.values()): unsched.append(dict(task_id=t["id"], reason=f"no bay supporting '{t['bay']}'"))
        else: ok.append(t)
    if not ok: raise OptimizerError("No schedulable maintenance tasks were found.")
    m = cp_model.CpModel(); V = {}; tech_iv = {k: [] for k in techs}; bay_iv = {k: [] for k in bays}; ac_iv = {}; part_late = {}
    obj = []
    for t in ok:
        i = t["id"]; s = m.NewIntVar(t["release"], min(H, t["release"] + t["flex"]) if t["kind"] != "predictive" else H, f"s_{i}")
        e = m.NewIntVar(0, H + t["dur"], f"e_{i}"); m.Add(e == s + t["dur"]); V[i] = (s, e, {}, {})
        ac_iv.setdefault(t["aircraft"], []).append(m.NewIntervalVar(s, t["dur"], e, f"a_{i}"))
        for k, v in techs.items():
            if t["skill"] in v["skills"]:
                x = m.NewBoolVar(f"x_{i}_{k}"); V[i][2][k] = x
                tech_iv[k].append(m.NewOptionalIntervalVar(s, t["dur"], e, x, f"ti_{i}_{k}")); m.Add(s >= v["free_at"]).OnlyEnforceIf(x)
        for k, v in bays.items():
            if t["bay"] in v["supports"]:
                y = m.NewBoolVar(f"y_{i}_{k}"); V[i][3][k] = y
                bay_iv[k].append(m.NewOptionalIntervalVar(s, t["dur"], e, y, f"bi_{i}_{k}")); m.Add(s >= v["free_at"]).OnlyEnforceIf(y)
        m.AddExactlyOne(V[i][2].values()); m.AddExactlyOne(V[i][3].values())
        if t["part"]:
            late = m.NewBoolVar(f"late_{i}"); part_late.setdefault(t["part"], []).append(late)
            m.Add(s >= spare_lead(t["part"])).OnlyEnforceIf(late)
        lateness = m.NewIntVar(0, H, f"l_{i}"); m.Add(lateness >= s - t["deadline"])
        obj += [t["weight"] * s, 5 * t["weight"] * lateness, e]
    for k in tech_iv: m.AddNoOverlap(tech_iv[k])
    for k in bay_iv: m.AddNoOverlap(bay_iv[k])
    for k in ac_iv: m.AddNoOverlap(ac_iv[k])
    for part, lates in part_late.items(): m.Add(sum(lates) >= len(lates) - spare_avail(part))  # at most 'available' tasks start without waiting for resupply
    m.Minimize(sum(obj))
    sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = 10; sol.parameters.random_seed = 1; sol.parameters.num_workers = 4
    st = sol.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise OptimizerError("Optimizer could not find a feasible schedule with the current technicians, bays and spares.")
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    rows, tl = [], {}
    for t in sorted(ok, key=lambda t: sol.Value(V[t["id"]][0])):
        s = sol.Value(V[t["id"]][0]); i = t["id"]
        tk = next(k for k, x in V[i][2].items() if sol.Value(x)); bk = next(k for k, y in V[i][3].items() if sol.Value(y))
        free_t, free_b = techs[tk]["free_at"], bays[bk]["free_at"]
        lead = spare_lead(t["part"]) if t["part"] else 0
        why = ("waiting for scheduled window" if s == t["release"] and t["release"] > 0 else f"spare resupply (+{lead} h)" if t["part"] and s == lead and spare_avail(t["part"]) < 1
               else f"{tk} busy until +{free_t} h" if s == free_t and free_t > 0 else f"{bk} busy until +{free_b} h" if s == free_b and free_b > 0 else "starts immediately" if s == 0 else "queued behind higher-impact work on shared technician/bay")
        risk = risk_before(t["p"], s) if t["p"] else 0
        rows.append(dict(task_id=i, aircraft=t["aircraft"], component=t["component"], task=t["label"], kind=t["kind"], technician=tk, technician_name=techs[tk]["name"], bay=bk, start=s, end=s + t["dur"],
                         start_label=(now + dt.timedelta(hours=s)).strftime("%a %H:%M"), end_label=(now + dt.timedelta(hours=s + t["dur"])).strftime("%a %H:%M"), spare=t["part"],
                         spare_status=("none" if not t["part"] else "on order" if spare_avail(t["part"]) < 1 else "reserved from stock"), priority=t["weight"], failure_prob=round(t["p"], 3),
                         risk_before_start=round(risk, 3), reason=why))
    for k, r in enumerate(rows): r["seq"] = k + 1
    before, after = _evaluate(baseline(build_tasks(False)), build_tasks(False)), _evaluate([dict(task_id=r["task_id"], start=r["start"], end=r["end"]) for r in rows], ok)
    plan = dict(status="OPTIMAL" if st == cp_model.OPTIMAL else "FEASIBLE", generated=now.isoformat(), horizon_h=H, schedule=rows, unschedulable=unsched, before=before, after=after,
                availability_gain_pts=round(after["projected_availability_pct"] - before["projected_availability_pct"], 2),
                baseline_description="FIFO by aircraft ID, no risk ordering, no bundling", applied=False,
                notes=[f"{sum(1 for r in rows if r['kind']=='bundled')} repair(s) bundled into scheduled inspections (saves {int((1-BUNDLE_FACTOR)*100)}% marginal downtime).",
                       f"{sum(1 for r in rows if r['spare_status']=='on order')} task(s) wait for spare resupply.",
                       "Objective: minimise impact-weighted start time and lateness versus RUL; constraints: technician skill/overlap, bay compatibility/overlap, spare stock, aircraft non-overlap."],
                label="Synthetic / simulated data for prototype demonstration.")
    if apply_persist:
        S.data["maintenance_plans"]["current"] = plan; S.commit("maintenance_plans")
    return plan


def apply_plan():
    plan = S.get("maintenance_plans/current")
    if not plan: raise OptimizerError("No plan to apply. Run the optimizer first.")
    if plan.get("applied"): raise OptimizerError("Plan already applied.")
    need = {}
    for r in plan["schedule"]:
        if r["spare"] and r["spare_status"] == "reserved from stock": need[r["spare"]] = need.get(r["spare"], 0) + 1
    for part, n in need.items():
        if spare_avail(part) < n: raise OptimizerError(f"Insufficient stock for {part}: need {n}, available {spare_avail(part)}.")
    for part, n in need.items(): S.data["spares"][part]["reserved"] += n
    for r in plan["schedule"]:
        for coll, k in (("technicians", r["technician"]), ("bays", r["bay"])):
            S.data[coll][k]["current_assignment"] = S.data[coll][k]["current_assignment"] or f"{r['task_id']} @+{r['start']}h"
        S.data["maintenance_tasks"][r["task_id"]] = dict(id=r["task_id"], aircraft=r["aircraft"], component=r["component"], kind=r["kind"], status="planned", label=r["task"],
                                                         technician=r["technician"], bay=r["bay"], start=r["start"], end=r["end"])
    plan["applied"] = True
    from .engine import refresh
    refresh(); S.commit("spares", "technicians", "bays", "maintenance_tasks", "maintenance_plans")
    return dict(applied=True, reserved=need)
