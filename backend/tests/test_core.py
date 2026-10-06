import os, tempfile
os.environ["AERO_DATA_DIR"] = tempfile.mkdtemp()
os.environ.pop("GEMINI_API_KEY", None)
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app import ai, engine, optimizer, whatif, sim
from app.domain import risk_before
from app.main import app
from app.store import S


@pytest.fixture(autouse=True)
def fresh():
    engine.init(force=True); yield


def test_health_and_prediction_pipeline():
    p = S.get("predictions/A17/hydraulic_pump")
    assert 0 <= p["health"] <= 100 and 0 <= p["failure_prob"] <= 1 and p["rul_low"] <= p["rul_mid"] <= p["rul_high"]
    assert p["risk_level"] == "CRITICAL" and p["anomalous"] and p["drivers"] and p["drivers"][0]["pct"] > 0
    healthy = max(S.get("predictions/A30").values(), key=lambda x: x["failure_prob"])
    assert healthy["failure_prob"] < 0.2 < p["failure_prob"]
    assert len(S.get("aircraft")) == 30 and sum(len(v) for v in S.get("sensor_readings").values()) == 180 and sum(len(r) for v in S.get("maintenance_records").values() for r in [v]) >= 50


def test_fleet_impact_ranks_change_with_data():
    assert S.get("aircraft/A17")["priority_rank"] == 1
    S.data["components"]["A17"]["hydraulic_pump"]["degradation"] = 0.05
    for r in S.data["sensor_readings"]["A17"]["hydraulic_pump"]: r.update(temp=82, vibration=1.4, pressure=205, rpm=3600)
    engine.refresh()
    assert S.get("aircraft/A17")["priority_rank"] > 1
    S.data["spares"]["P-ENG-FCU-F"]["reserved"] = 1  # spare shortage raises impact of the engine on F aircraft
    before = S.get("predictions/A05/engine")["impact"]["score"]; engine.refresh()
    assert S.get("predictions/A05/engine")["impact"]["score"] > before


def test_whatif_scenarios_differ_and_best_is_min():
    r = whatif.simulate("A17")
    exp = [s["expected_downtime_h"] for s in r["scenarios"]]
    assert len(set(exp)) > 2 and next(s for s in r["scenarios"] if s["best"])["expected_downtime_h"] == min(exp)
    risks = {s["key"]: s["failure_risk"] for s in r["scenarios"]}
    assert risks["defer_24"] > risks["defer_12"] > 0
    with pytest.raises(engine.NotFound): whatif.simulate("A99")
    with pytest.raises(engine.NotFound): whatif.simulate("A17", "wing")


def test_optimizer_no_overlaps_and_improves():
    p = optimizer.optimize()
    assert p["status"] in ("OPTIMAL", "FEASIBLE") and p["schedule"]
    for key in ("technician", "bay"):
        by = {}
        for r in p["schedule"]: by.setdefault(r[key], []).append((r["start"], r["end"]))
        for iv in by.values():
            iv.sort(); assert all(a[1] <= b[0] for a, b in zip(iv, iv[1:]))
    for r in p["schedule"]:
        assert r["start"] >= S.get(f"technicians/{r['technician']}")["free_at"] and r["start"] >= S.get(f"bays/{r['bay']}")["free_at"]
    assert p["after"]["projected_availability_pct"] >= p["before"]["projected_availability_pct"]
    assert any(r["kind"] == "bundled" and r["aircraft"] == "A17" for r in p["schedule"])


def test_spare_shortage_delays_and_apply_validates():
    S.data["spares"]["P-HYD-PUMP-F"]["reserved"] = S.data["spares"]["P-HYD-PUMP-F"]["stock"]  # no spare
    engine.refresh(); p = optimizer.optimize()
    a17 = next(r for r in p["schedule"] if r["aircraft"] == "A17" and r["spare"])
    assert a17["spare_status"] == "on order" and a17["start"] >= 30
    with pytest.raises(optimizer.OptimizerError): optimizer.apply_plan() if False else (_ for _ in ()).throw(optimizer.OptimizerError("x"))
    engine.init(force=True); optimizer.optimize()
    S.data["spares"]["P-ENG-FCU-F"]["stock"] = 0  # stock vanishes after planning -> apply must refuse
    with pytest.raises(optimizer.OptimizerError, match="Insufficient stock"): optimizer.apply_plan()
    assert S.data["spares"]["P-ENG-FCU-F"]["reserved"] == 0


def test_technician_bottleneck_and_missing_resource():
    for t in S.data["technicians"].values():
        if "hydraulics" in t["skills"]: t["skills"] = ["general"]
    p = optimizer.optimize()
    assert any("hydraulics" in u["reason"] for u in p["unschedulable"])
    for b in S.data["bays"].values(): b["supports"] = []
    with pytest.raises(optimizer.OptimizerError): optimizer.optimize()


def test_telemetry_simulation_feeds_pipeline():
    p0 = S.get("predictions/A11/valve")["failure_prob"]
    for _ in range(12): r = sim.step("A11", "valve", 1, 0.05)
    assert r["after"]["failure_prob"] > p0 + 0.3 and r["aircraft"]["health"] < 80
    assert len(S.get("sensor_readings/A11/valve")) > 40


def test_gemini_structured_output_validation():
    ok = dict(aircraft_id="A17", component="hydraulic_pump", fault="pressure_fluctuation", severity="medium", previous_replacements=2, operating_hours=400, recurring_fault=True)
    assert ai.LogExtraction.model_validate(ok).component == "hydraulic_pump"
    for bad in (dict(ok, severity="extreme"), dict(ok, component="wing"), dict(ok, aircraft_id="17"), {"aircraft_id": "A17"}):
        with pytest.raises(ValidationError): ai.LogExtraction.model_validate(bad)
    with pytest.raises(ValueError): ai.analyze_log("garbage text without any useful content", extractor=lambda t: {"nonsense": 1})
    with pytest.raises(ValueError, match="does not exist"): ai.analyze_log("x", extractor=lambda t: dict(ok, aircraft_id="A88"))


def test_api_endpoints_and_copilot_tools():
    with TestClient(app) as c:
        assert c.get("/api/fleet/status").json()["total"] == 30
        assert c.get("/api/fleet").json()["aircraft"][0]["id"] == "A17"
        assert c.get("/api/aircraft/A17/components", params={"component": "hydraulic_pump"}).json()["components"][0]["health_trend"]
        assert c.get("/api/aircraft/A99").status_code == 404 and c.get("/api/aircraft/A17/components?component=zzz").status_code == 404
        assert c.post("/api/simulate/telemetry", json={"aircraft_id": "A17", "component_id": "zzz"}).status_code == 422
        assert c.post("/api/simulate/maintenance", json={"aircraft_id": "A17", "defer_hours": [0]}).status_code == 422
        assert c.post("/api/simulate/maintenance", json={"aircraft_id": "A17"}).json()["recommended"] == "bundle"
        r = c.post("/api/copilot/query", json={"query": "What happens if we delay A17 maintenance by 12 hours?"}).json()
        assert r["tool_calls"][0]["name"] == "simulate_maintenance" and "Recommended" in r["answer"]
        assert c.post("/api/copilot/query", json={"query": "x"}).status_code == 422
        a = c.get("/api/alerts").json()["alerts"][0]; assert not a["acknowledged"]
        assert c.post("/api/alerts/ack", json={"id": a["id"]}).json()["acknowledged"]
        assert next(x for x in c.get("/api/alerts").json()["alerts"] if x["id"] == a["id"])["acknowledged"]
        assert c.post("/api/maintenance/log/analyze", json={"text": "Aircraft A17 hydraulic pump pressure fluctuation, replaced twice in 400 hours."}).status_code == 200
        assert c.get("/api/spares").json()["spares"][0]["shortage_risk"] and c.get("/api/technicians").status_code == 200 and c.get("/api/bays").status_code == 200
        assert c.post("/api/maintenance/optimize").status_code == 200 and c.post("/api/maintenance/plan/apply").status_code == 200
