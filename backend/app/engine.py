"""Core engine: predictions -> fleet impact -> aircraft summaries -> alerts -> KPIs."""
import math
from .domain import COMPONENTS, HORIZON_H, risk_level
from .store import S
from . import seed as seed_mod
from .ml import models


class NotFound(Exception): pass


def spare_avail(part):
    sp = S.get("spares", {}).get(part)
    return (sp["stock"] - sp["reserved"]) if sp else 0


def spare_lead(part):
    sp = S.get("spares", {}).get(part)
    return sp["lead_time_h"] if sp else 24


def waits(skill, bay):
    techs = [t for t in S.get("technicians").values() if skill in t["skills"]]
    bays = [b for b in S.get("bays").values() if bay in b["supports"]]
    if not techs: raise NotFound(f"No technician with skill '{skill}'")
    if not bays: raise NotFound(f"No maintenance bay supporting '{bay}'")
    return min(t["free_at"] for t in techs), min(b["free_at"] for b in bays)


def impact(aid, cid, pred):
    c, comp = COMPONENTS[cid], S.get(f"components/{aid}/{cid}")
    short = spare_avail(comp["part_id"]) < 1
    down = c["repair"] + (spare_lead(comp["part_id"]) if short else 0)
    prio = {1: 1.5, 2: 1.15, 3: 1.0}[S.get(f"aircraft/{aid}")["op_priority"]]
    raw = pred["failure_prob"] * c["crit"] * (down / 24) * prio * (1.25 if short else 1.0)
    score = round(100 * (1 - math.exp(-1.6 * raw)), 1)
    return dict(score=score, level="HIGH" if score >= 55 else "MEDIUM" if score >= 25 else "LOW", expected_downtime_h=down, spare_short=short,
                criticality=c["crit"], op_priority=S.get(f"aircraft/{aid}")["op_priority"],
                formula="100*(1-exp(-1.6 * P(fail) * criticality * downtime/24 * priority_factor * spare_factor))")


def refresh(aids=None):
    rows, keys = [], []
    for aid, comps in S.get("components").items():
        if aids and aid not in aids: continue
        for cid, c in comps.items():
            rd = S.get(f"sensor_readings/{aid}/{cid}")
            rows.append(dict(comp_id=cid, readings=rd[-5:], n=len(rd), hours_ratio=c["hours_since_overhaul"] / c["overhaul_interval"], prev=c["prev_failures"]))
            keys.append((aid, cid))
    for (aid, cid), p in zip(keys, models().predict_many(rows)):
        p["impact"] = impact(aid, cid, p)
        S.data["predictions"].setdefault(aid, {})[cid] = p
    for aid in S.get("aircraft"):  # impact depends on spares for every aircraft; recompute cheaply
        for cid, p in S.data["predictions"].get(aid, {}).items():
            p["impact"] = impact(aid, cid, p)
    summarize()
    gen_alerts()
    S.commit("predictions", "aircraft", "alerts")


def summarize():
    for aid, ac in S.get("aircraft").items():
        preds = S.get(f"predictions/{aid}", {})
        if not preds: continue
        w = {cid: COMPONENTS[cid]["crit"] for cid in preds}
        wmean = sum(preds[c]["health"] * w[c] for c in preds) / sum(w.values())
        worst = max(preds, key=lambda c: preds[c]["failure_prob"])
        top = max(preds, key=lambda c: preds[c]["impact"]["score"])
        task = next((t for t in S.get("maintenance_tasks").values() if t["aircraft"] == aid and t["status"] == "in_progress"), None)
        p = preds[worst]["failure_prob"]
        status = "MAINTENANCE" if task else "CRITICAL" if p >= 0.7 else "DEGRADED" if p >= 0.25 else "READY"
        ac.update(health=round(0.5 * min(v["health"] for v in preds.values()) + 0.5 * wmean, 1), failure_risk=round(p, 3), risk_level=risk_level(p),
                  worst_component=worst, rul_low=preds[worst]["rul_low"], rul_high=preds[worst]["rul_high"], status=status,
                  impact_score=preds[top]["impact"]["score"], impact_level=preds[top]["impact"]["level"], top_impact_component=top,
                  current_task=f"{task['label']} ({task['remaining_h']}h left)" if task else None)
    ranked = sorted(S.get("aircraft").values(), key=lambda a: -a.get("impact_score", 0))
    for i, a in enumerate(ranked): a["priority_rank"] = i + 1


def gen_alerts():
    old, new = S.get("alerts", {}), {}
    def add(typ, aid, cid, sev, msg):
        k = f"{typ}|{aid}|{cid or '-'}"
        new[k] = dict(id=k, type=typ, aircraft_id=aid, component_id=cid, severity=sev, message=msg,
                      acknowledged=old.get(k, {}).get("acknowledged", False), ack_at=old.get(k, {}).get("ack_at"))
    need = {}
    for aid, comps in S.get("predictions").items():
        for cid, p in comps.items():
            lab = COMPONENTS[cid]["label"]
            if p["failure_prob"] >= 0.5: add("HIGH_FAILURE_PROB", aid, cid, "critical" if p["failure_prob"] >= 0.7 else "high", f"{aid} {lab}: failure probability {p['failure_prob']*100:.0f}%")
            if p["anomalous"] and p["failure_prob"] >= 0.2: add("ABNORMAL_TELEMETRY", aid, cid, "medium", f"{aid} {lab}: anomalous telemetry (score {p['anomaly_score']:.2f})")
            if p["rul_low"] < 24 and p["failure_prob"] >= 0.3: add("LOW_RUL", aid, cid, "high", f"{aid} {lab}: RUL {p['rul_low']:.0f}-{p['rul_high']:.0f} h")
            if p["impact"]["level"] == "HIGH": add("CRITICAL_FLEET_IMPACT", aid, cid, "high", f"{aid} {lab}: fleet impact {p['impact']['score']:.0f}/100")
            if p["failure_prob"] >= 0.3:
                part = S.get(f"components/{aid}/{cid}")["part_id"]; need.setdefault(COMPONENTS[cid]["skill"], []).append((aid, cid))
                if spare_avail(part) < 1: add("SPARE_SHORTAGE", aid, cid, "high", f"{part}: no spare available for {aid} {lab} (lead {spare_lead(part)} h)")
    for skill, items in need.items():
        n = len([t for t in S.get("technicians").values() if skill in t["skills"]])
        if len(items) > n:
            aid, cid = items[0]; add("MAINTENANCE_CONFLICT", aid, None, "medium", f"Demand for '{skill}' work ({len(items)} jobs) exceeds {n} qualified technician(s)")
    S.data["alerts"] = new


def kpis():
    ac = list(S.get("aircraft").values()); n = len(ac)
    cnt = lambda s: sum(a["status"] == s for a in ac)
    sp = list(S.get("spares").values()); t = list(S.get("technicians").values()); b = list(S.get("bays").values())
    return dict(total=n, ready=cnt("READY"), degraded=cnt("DEGRADED"), critical=cnt("CRITICAL"), maintenance=cnt("MAINTENANCE"),
                fleet_availability_pct=round(100 * (cnt("READY") + cnt("DEGRADED")) / n, 1),
                critical_alerts=sum(1 for a in S.get("alerts").values() if a["severity"] in ("critical", "high") and not a["acknowledged"]),
                active_tasks=sum(1 for x in S.get("maintenance_tasks").values() if x["status"] == "in_progress"),
                spare_availability_pct=round(100 * sum(1 for s in sp if s["stock"] - s["reserved"] > 0) / len(sp), 1),
                parts_short=[s["part_id"] for s in sp if s["stock"] - s["reserved"] < 1],
                technicians_free=sum(1 for x in t if x["free_at"] == 0), technicians_total=len(t),
                bays_free=sum(1 for x in b if x["free_at"] == 0), bays_total=len(b), label="Synthetic / simulated data for prototype demonstration.")


def init(force=False):
    if force or not S.load():
        seed_mod.seed(); S.commit()
    refresh()
