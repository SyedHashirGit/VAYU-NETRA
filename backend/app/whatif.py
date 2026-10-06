"""What-if simulator: deterministic comparison of repair-now / defer / bundle for one component."""
import math
from .domain import COMPONENTS, HORIZON_H, risk_before, unplanned_penalty
from .engine import S, NotFound, spare_avail, spare_lead, waits

BUNDLE_FACTOR = 0.55  # marginal downtime fraction when work is done inside an already-open scheduled inspection


def fleet_base_downtime(exclude_sched=None):
    t = S.get("maintenance_tasks").values()
    return sum(x.get("remaining_h", 0) for x in t if x["status"] == "in_progress") + sum(x["duration"] for x in t if x["status"] == "scheduled")


def simulate(aid, cid=None, defer_hours=(6, 12, 24)):
    ac = S.get(f"aircraft/{aid}")
    if not ac: raise NotFound(f"Aircraft '{aid}' not found")
    preds = S.get(f"predictions/{aid}", {})
    cid = cid or ac["worst_component"]
    if cid not in preds: raise NotFound(f"Component '{cid}' not found on {aid}")
    p, meta, comp = preds[cid], COMPONENTS[cid], S.get(f"components/{aid}/{cid}")
    R, part = meta["repair"], comp["part_id"]
    tw, bw = waits(meta["skill"], meta["bay"])
    avail = spare_avail(part)
    lead = 0 if avail >= 1 else spare_lead(part)
    ready = max(tw, bw, lead)
    sched = next((t for t in S.get("maintenance_tasks").values() if t["aircraft"] == aid and t["status"] == "scheduled"), None)
    n, base = len(S.get("aircraft")), fleet_base_downtime()
    pen = unplanned_penalty(R)
    spare_txt = "in stock" if avail > 1 else "uses last available unit" if avail == 1 else f"SHORTAGE: on order, +{lead} h"

    def scenario(key, name, start, down, note):
        risk = risk_before(p["failure_prob"], start)
        exp = down + risk * pen
        return dict(key=key, name=name, start_h=round(start, 1), planned_downtime_h=round(down, 1), failure_risk=round(risk, 4),
                    expected_downtime_h=round(exp, 1), fleet_availability_pct=round(100 * (1 - (base + exp) / (n * HORIZON_H)), 2),
                    spare=spare_txt, spare_consumed=1, workload_tech_h=round(down, 1), note=note)
    out = [scenario("repair_now", "Repair immediately", ready, R, f"Starts at +{ready:.0f} h (first free technician/bay{', spare lead' if lead else ''}).")]
    for h in defer_hours:
        out.append(scenario(f"defer_{h}", f"Defer {h} h", max(h, ready), R, f"Aircraft keeps flying {max(h, ready):.0f} h before repair."))
    if sched:
        out.append(scenario("bundle", f"Bundle with scheduled inspection (+{sched['window_start']} h)", max(sched["window_start"], lead), math.ceil(BUNDLE_FACTOR * R),
                            f"Shares access/teardown with SM inspection; marginal downtime {BUNDLE_FACTOR:.0%} of standalone."))
    best = min(out, key=lambda s: (s["expected_downtime_h"], s["failure_risk"]))
    for s in out: s["best"] = s is best
    runner = sorted(out, key=lambda s: s["expected_downtime_h"])[1]
    why = [f"{best['name']} has the lowest expected downtime: {best['expected_downtime_h']} h versus {runner['expected_downtime_h']} h for {runner['name']}.",
           f"Failure risk before work starts is {best['failure_risk']*100:.0f}% (P(fail within 50h) = {p['failure_prob']*100:.0f}%, RUL {p['rul_low']:.0f}-{p['rul_high']:.0f} h).",
           f"An in-service failure costs about {pen:.0f} h of downtime (1.5 x repair + 12 h), so waiting is penalised by risk x {pen:.0f} h.",
           f"Resources: earliest qualified technician free at +{tw} h, bay at +{bw} h; spare {part}: {spare_txt}."]
    if not sched: why.append("No scheduled inspection window exists for this aircraft, so bundling is not available.")
    return dict(aircraft_id=aid, component_id=cid, component=meta["label"], part_id=part, current=dict(failure_prob=p["failure_prob"], rul_low=p["rul_low"], rul_high=p["rul_high"], health=p["health"],
                impact=p["impact"], fleet_availability_now_pct=round(100 * (1 - base / (n * HORIZON_H)), 2)),
                scenarios=out, recommended=best["key"], why=why, label="Synthetic / simulated data for prototype demonstration.")
