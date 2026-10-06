"""Telemetry simulator: advances degradation, appends a reading, re-runs the real prediction pipeline."""
import numpy as np
from .engine import S, NotFound, refresh
from .ml import make_reading

_rng = np.random.default_rng(99)


def step(aid, cid, steps=1, rate=0.02):
    comp = S.get(f"components/{aid}/{cid}")
    if comp is None: raise NotFound(f"Component '{cid}' on aircraft '{aid}' not found")
    before = dict(S.get(f"predictions/{aid}/{cid}"))
    rd = S.data["sensor_readings"][aid][cid]
    for _ in range(steps):
        comp["degradation"] = min(0.98, comp["degradation"] + rate)
        comp["hours_since_overhaul"] += 1
        r = make_reading(cid, comp["degradation"], _rng, noise=0.3); r = {k: round(v, 3) for k, v in r.items()}; r["h"] = rd[-1]["h"] + 1
        rd.append(r); del rd[:-60]
    S.data["simulation"].update(aircraft_id=aid, component_id=cid, tick=S.get("simulation/tick", 0) + steps)
    refresh({aid}); S.commit(f"components/{aid}/{cid}", f"sensor_readings/{aid}/{cid}", "simulation")
    after = S.get(f"predictions/{aid}/{cid}")
    return dict(aircraft_id=aid, component_id=cid, degradation=round(comp["degradation"], 3), latest_reading=rd[-1],
                before={k: before[k] for k in ("failure_prob", "health", "rul_low", "rul_high", "anomaly_score")},
                after={k: after[k] for k in ("failure_prob", "health", "rul_low", "rul_high", "anomaly_score")},
                aircraft=S.get(f"aircraft/{aid}"))
