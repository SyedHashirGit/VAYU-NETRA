"""ML layer: Isolation Forest (anomaly), GradientBoosting classifier (failure probability within 50h),
GradientBoosting quantile regressors (RUL range). Trained at start-up on SYNTHETIC degradation data.
Not validated against any real aircraft data."""
import numpy as np
from sklearn.ensemble import IsolationForest, GradientBoostingClassifier, GradientBoostingRegressor
from .domain import COMPONENTS, risk_level

FEATS = ["temp_dev", "vib_dev", "press_dev", "rpm_dev", "hours_ratio", "prev_failures"]
FEAT_LABEL = {"temp_dev": "Temperature drift", "vib_dev": "Vibration anomaly", "press_dev": "Pressure instability",
              "rpm_dev": "RPM deviation", "hours_ratio": "Operating hours since overhaul", "prev_failures": "Previous failures"}
BASELINE = np.array([0, 0, 0, 0, 0.3, 0.0])


def make_reading(cid, d, rng, noise=1.0):
    b = COMPONENTS[cid]["base"]
    return dict(temp=b["temp"] * (1 + 0.28 * d ** 1.3 + rng.normal(0, 0.012 * noise)),
                vibration=b["vibration"] * (1 + 2.2 * d ** 1.5 + rng.normal(0, 0.04 * noise)),
                pressure=b["pressure"] * (1 - 0.12 * d + rng.normal(0, (0.01 + 0.05 * d) * noise)),
                rpm=b["rpm"] * (1 - 0.06 * d + rng.normal(0, (0.01 + 0.02 * d) * noise)))


def features(cid, readings, hours_ratio, prev):
    b = COMPONENTS[cid]["base"]
    t = np.mean([r["temp"] for r in readings]); v = np.mean([r["vibration"] for r in readings])
    p = np.array([r["pressure"] for r in readings]); n = np.mean([r["rpm"] for r in readings])
    return [(t - b["temp"]) / b["temp"], (v - b["vibration"]) / b["vibration"],
            (b["pressure"] - p.mean()) / b["pressure"] + 2 * p.std() / b["pressure"], (b["rpm"] - n) / b["rpm"],
            hours_ratio, prev]


class Models:
    def __init__(self, seed=11):
        rng = np.random.default_rng(seed)
        X, y, rul, X_ok = [], [], [], []
        cids = list(COMPONENTS)
        for _ in range(5000):
            cid = cids[rng.integers(len(cids))]
            d = float(rng.uniform(0, 1) if rng.random() < 0.7 else rng.uniform(0.4, 1))
            hr, prev = float(rng.uniform(0, 1.3)), int(rng.poisson(0.6))
            f = features(cid, [make_reading(cid, d, rng) for _ in range(5)], hr, prev)
            logit = 9 * (d - 0.6) + 1.2 * (hr - 0.8) + 0.5 * prev
            X.append(f); y.append(int(rng.random() < 1 / (1 + np.exp(-logit))))
            rul.append(max(2.0, 140 * (1 - d) ** 1.2 / (1 + 0.2 * prev) * (1.3 - 0.4 * hr) * float(np.exp(rng.normal(0, 0.15)))))
            if d < 0.25:
                X_ok.append(f[:4])
        X, y, rul = np.array(X), np.array(y), np.array(rul)
        self.iso = IsolationForest(n_estimators=150, contamination=0.02, random_state=seed).fit(np.array(X_ok))
        self.clf = GradientBoostingClassifier(n_estimators=120, max_depth=3, random_state=seed).fit(X, y)
        kw = dict(n_estimators=100, max_depth=3, random_state=seed)
        self.r_lo = GradientBoostingRegressor(loss="quantile", alpha=0.1, **kw).fit(X, rul)
        self.r_mid = GradientBoostingRegressor(loss="quantile", alpha=0.5, **kw).fit(X, rul)
        self.r_hi = GradientBoostingRegressor(loss="quantile", alpha=0.9, **kw).fit(X, rul)

    def predict_many(self, rows):
        """rows: dicts with comp_id, readings (recent), n, hours_ratio, prev."""
        if not rows:
            return []
        X = np.array([features(r["comp_id"], r["readings"], r["hours_ratio"], r["prev"]) for r in rows])
        p = self.clf.predict_proba(X)[:, 1]
        sc = -self.iso.score_samples(X[:, :4]); lab = self.iso.predict(X[:, :4])
        anom = np.clip((sc - 0.44) / 0.3, 0, 1)
        lo, mid, hi = (m.predict(X) for m in (self.r_lo, self.r_mid, self.r_hi))
        # transparent feature contributions: drop in P(fail) when one feature is reset to a healthy baseline
        contrib = np.zeros_like(X)
        for j in range(X.shape[1]):
            Xb = X.copy(); Xb[:, j] = BASELINE[j]
            contrib[:, j] = p - self.clf.predict_proba(Xb)[:, 1]
        out = []
        for i, r in enumerate(rows):
            a, b, c = sorted([max(1.0, lo[i]), max(1.0, mid[i]), max(1.0, hi[i])])
            width = (c - a) / (a + c + 1)
            conf = float(np.clip(0.92 - 0.5 * width, 0.3, 0.95) * min(1.0, r["n"] / 20))
            drivers = sorted([dict(feature=FEATS[j], label=FEAT_LABEL[FEATS[j]], pct=round(float(contrib[i, j]) * 100, 1))
                              for j in range(len(FEATS)) if contrib[i, j] > 0.005], key=lambda x: -x["pct"])[:4]
            pi = float(p[i])
            out.append(dict(failure_prob=round(pi, 4), risk_level=risk_level(pi), anomaly_score=round(float(anom[i]), 3),
                            anomalous=bool(lab[i] == -1), rul_low=round(float(a), 1), rul_mid=round(float(b), 1), rul_high=round(float(c), 1),
                            confidence=round(conf, 2), health=round(100 * (1 - (0.65 * pi + 0.35 * float(anom[i]))), 1),
                            drivers=drivers, features={FEATS[j]: round(float(X[i, j]), 4) for j in range(len(FEATS))}))
        return out


_models = None
def models():
    global _models
    if _models is None:
        _models = Models()
    return _models
