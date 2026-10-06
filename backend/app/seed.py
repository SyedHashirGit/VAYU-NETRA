"""Reproducible seed of synthetic demo data. Synthetic / simulated data for prototype demonstration."""
import numpy as np
from .domain import COMPONENTS, MODELS
from .store import S, ROOTS
from .ml import make_reading

# (aircraft, component) -> degradation level d (0 healthy .. 1 failed)
DEGRADED = {("A17", "hydraulic_pump"): 0.68, ("A05", "engine"): 0.50, ("A09", "landing_gear"): 0.58, ("A22", "avionics"): 0.44,
            ("A12", "fuel_pump"): 0.42, ("A28", "valve"): 0.38, ("A14", "engine"): 0.33, ("A07", "hydraulic_pump"): 0.30}
PREV = {("A17", "hydraulic_pump"): 2, ("A05", "engine"): 1, ("A09", "landing_gear"): 1, ("A22", "avionics"): 1}
SCHEDULED = {"A17": 10, "A02": 6, "A06": 30, "A09": 26, "A14": 22, "A20": 44, "A22": 18, "A28": 36, "A05": 40}
SKILLS = [("T01", "Ravi N.", ["engine"]), ("T02", "Imran K.", ["engine", "general"]), ("T03", "Meera S.", ["avionics"]),
          ("T04", "Arjun P.", ["hydraulics"]), ("T05", "Kiran D.", ["hydraulics"]), ("T06", "Suresh L.", ["landing", "general"]),
          ("T07", "Anita R.", ["general", "fuel"]), ("T08", "Vikram J.", ["avionics", "general"]), ("T09", "Dev M.", ["landing", "fuel"]),
          ("T10", "Farhan A.", ["engine"]), ("T11", "Nisha T.", ["general"]), ("T12", "Pooja V.", ["fuel", "general"])]
BAYS = [("B01", "Bay 1 Engine", ["engine"]), ("B02", "Bay 2 Hydraulics", ["hydraulics"]), ("B03", "Bay 3 Avionics", ["avionics"]),
        ("B04", "Bay 4 General/Avionics", ["general", "avionics"]), ("B05", "Bay 5 General", ["general"]), ("B06", "Bay 6 Engine/General", ["engine", "general"])]


def seed():
    rng = np.random.default_rng(7)
    S.data = {r: {} for r in ROOTS}
    aids = [f"A{i:02d}" for i in range(1, 31)]
    for i, aid in enumerate(aids):
        code = "F" if i % 3 != 2 else ("T" if i % 2 else "R")
        S.data["aircraft"][aid] = dict(id=aid, model=MODELS[code], model_code=code, op_priority=1 if (code == "F" and i % 2 == 0) or aid == "A17" else 2 if code == "F" else 3,
                                       total_hours=int(rng.integers(800, 4200)), scheduled_window_h=SCHEDULED.get(aid))
        S.data["components"][aid], S.data["sensor_readings"][aid], S.data["maintenance_records"][aid] = {}, {}, {}
        for cid, c in COMPONENTS.items():
            d = DEGRADED.get((aid, cid), float(rng.beta(1.2, 9) * 0.3))
            prev = PREV.get((aid, cid), int(rng.random() < 0.15))
            hrs = int(c["interval"] * rng.uniform(0.25, 0.85)) if (aid, cid) not in PREV else int(c["interval"] * 0.8)
            S.data["components"][aid][cid] = dict(aircraft_id=aid, component_id=cid, label=c["label"], hours_since_overhaul=hrs, overhaul_interval=c["interval"],
                                                  prev_failures=prev, degradation=d, last_inspection_h_ago=int(rng.integers(5, 120)), part_id=f"{c['part']}-{code}")
            ramp = 0.18 if (aid, cid) in DEGRADED else 0.02
            rd = []
            for k in range(40):
                dk = max(0.0, d - ramp * (39 - k) / 39)
                r = make_reading(cid, dk, rng); r["h"] = -(39 - k); rd.append({kk: round(v, 3) if kk != "h" else v for kk, v in r.items()})
            S.data["sensor_readings"][aid][cid] = rd
    # maintenance history (60+ records)
    n = 0
    def rec(aid, cid, ago, typ, fault, note):
        nonlocal n; n += 1
        S.data["maintenance_records"][aid][f"R{n:03d}"] = dict(id=f"R{n:03d}", aircraft_id=aid, component_id=cid, hours_ago=ago, type=typ, fault=fault, note=note, source="seed")
    for aid in aids:
        for cid in rng.choice(list(COMPONENTS), 2, replace=False):
            rec(aid, str(cid), int(rng.integers(50, 900)), "inspection", "none", "Routine inspection, no findings.")
    for (aid, cid), k in PREV.items():
        for j in range(k):
            rec(aid, cid, 150 + 220 * j, "replacement", "recurring_fault", f"{COMPONENTS[cid]['label']} replaced after fault recurrence.")
    for aid, cid, f in [("A03", "engine", "overtemp"), ("A11", "valve", "leak"), ("A16", "fuel_pump", "pressure_loss"), ("A21", "landing_gear", "actuator_stall"),
                        ("A25", "avionics", "module_reset"), ("A08", "hydraulic_pump", "pressure_fluctuation"), ("A19", "engine", "vibration")] * 2:
        rec(aid, cid, int(rng.integers(200, 1500)), "failure", f, "Historical failure, component replaced and returned to service.")
    rec("A17", "hydraulic_pump", 30, "inspection", "pressure_fluctuation", "Post-flight check: intermittent hydraulic pressure fluctuation noted.")
    # spares: base part x model (18) + 4 consumables
    for cid, c in COMPONENTS.items():
        for code in "FTR":
            S.data["spares"][f"{c['part']}-{code}"] = dict(part_id=f"{c['part']}-{code}", component=cid, model_code=code, stock=int(rng.integers(2, 5)), min_stock=1,
                                                           reserved=0, location=f"Store {rng.choice(['N', 'S'])}-{int(rng.integers(1, 9))}", lead_time_h=int(rng.integers(18, 40)))
    for pid, cmp_, st in [("P-SEAL-KIT", "hydraulic_pump", 6), ("P-FILTER-HYD", "valve", 8), ("P-BRK-PAD", "landing_gear", 10), ("P-O-RING", "fuel_pump", 12)]:
        S.data["spares"][pid] = dict(part_id=pid, component=cmp_, model_code="*", stock=st, min_stock=3, reserved=0, location="Store C-1", lead_time_h=12)
    S.data["spares"]["P-HYD-PUMP-F"].update(stock=2, reserved=1, min_stock=2, lead_time_h=30)   # limited: 1 available
    S.data["spares"]["P-AVN-MOD-F"].update(stock=1, reserved=1, min_stock=2, lead_time_h=36)    # shortage: 0 available
    S.data["spares"]["P-ENG-FCU-F"].update(stock=1, reserved=0, min_stock=2, lead_time_h=48)
    # technicians / bays; free_at = hours until free
    for tid, nm, sk in SKILLS:
        S.data["technicians"][tid] = dict(id=tid, name=nm, skills=sk, free_at=0, current_assignment=None)
    for bid, nm, sup in BAYS:
        S.data["bays"][bid] = dict(id=bid, name=nm, supports=sup, free_at=0, current_assignment=None)
    S.data["technicians"]["T04"].update(free_at=11, current_assignment="Shift handover (unavailable)")  # hydraulics bottleneck
    for tid, bid, aid, cid, h in [("T05", "B02", "A11", "valve", 6), ("T01", "B01", "A03", "engine", 9), ("T03", "B03", "A25", "avionics", 4)]:
        tk = f"IP-{aid}"
        S.data["maintenance_tasks"][tk] = dict(id=tk, aircraft=aid, component=cid, kind="in_progress", status="in_progress", remaining_h=h, technician=tid, bay=bid, label=f"{COMPONENTS[cid]['label']} repair")
        S.data["technicians"][tid].update(free_at=h, current_assignment=tk)
        S.data["bays"][bid].update(free_at=h, current_assignment=tk)
    for aid, w in SCHEDULED.items():
        S.data["maintenance_tasks"][f"SM-{aid}"] = dict(id=f"SM-{aid}", aircraft=aid, component="inspection", kind="scheduled", status="scheduled", window_start=w, duration=10, label="Scheduled periodic inspection")
    S.data["simulation"] = dict(running=False, aircraft_id="A17", component_id="hydraulic_pump", tick=0)
    S.data["system_config"] = dict(label="Synthetic / simulated data for prototype demonstration.", horizon_h=72, seed=7)
    return S.data
