"""Static domain definitions. All data in this prototype is synthetic / simulated."""
import math

COMPONENTS = {
    "engine":         dict(label="Engine",         crit=1.00, repair=24, part="P-ENG-FCU",  skill="engine",     bay="engine",     interval=1500, base=dict(temp=620, pressure=45,  vibration=2.0, rpm=9800)),
    "hydraulic_pump": dict(label="Hydraulic Pump", crit=0.90, repair=14, part="P-HYD-PUMP", skill="hydraulics", bay="hydraulics", interval=1200, base=dict(temp=82,  pressure=205, vibration=1.4, rpm=3600)),
    "valve":          dict(label="Hydraulic Valve",crit=0.60, repair=6,  part="P-HYD-VLV",  skill="hydraulics", bay="hydraulics", interval=1000, base=dict(temp=75,  pressure=200, vibration=0.8, rpm=900)),
    "avionics":       dict(label="Avionics",       crit=0.80, repair=8,  part="P-AVN-MOD",  skill="avionics",   bay="avionics",   interval=2000, base=dict(temp=48,  pressure=3.0, vibration=0.3, rpm=6000)),
    "landing_gear":   dict(label="Landing System", crit=0.85, repair=12, part="P-LDG-ACT",  skill="landing",    bay="general",    interval=1400, base=dict(temp=55,  pressure=180, vibration=1.0, rpm=300)),
    "fuel_pump":      dict(label="Fuel System",    crit=0.75, repair=9,  part="P-FUEL-PMP", skill="fuel",       bay="general",    interval=1300, base=dict(temp=60,  pressure=5.0, vibration=1.1, rpm=4200)),
}
MODELS = {"F": "FTR-A (fighter)", "T": "TRP-B (transport)", "R": "TRN-C (trainer)"}
HORIZON_H = 72
LABEL = "Synthetic / simulated data for prototype demonstration."


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def risk_level(p):
    return "CRITICAL" if p >= 0.7 else "HIGH" if p >= 0.5 else "MEDIUM" if p >= 0.25 else "LOW"


def risk_before(p50, t):
    """P(failure before t hours) given P(failure within 50h)=p50 (constant-hazard assumption)."""
    p50 = min(max(p50, 0.0), 0.999)
    return 1 - (1 - p50) ** (max(t, 0) / 50.0)


def unplanned_penalty(repair_h):
    """Downtime if the component fails in service: grounding + secondary damage + recovery."""
    return 1.5 * repair_h + 12
