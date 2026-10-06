# VAYU-NETRA

Predict failures. Simulate consequences. Prescribe the optimal action.
SIH 2026, PS 26249 (Air Power: Predictive Maintenance & Fleet Availability).

**All data is synthetic / simulated for prototype demonstration. This is a decision-support prototype. It uses no real aircraft data and makes no claim of operational accuracy, deployment, or certification.**

## Architecture
```
Telemetry -> Isolation Forest + GradientBoosting (P fail 50h) + quantile GBR (RUL)
          -> Fleet Impact score -> What-if simulator -> OR-Tools CP-SAT optimizer -> plan
Store: Firebase Realtime DB (Admin SDK, backend only) or local JSON when Firebase env vars are absent
Gemini 2.5 Flash: copilot (function calling over backend tools) + maintenance-note extraction (JSON schema + Pydantic)
Gemini never produces numbers. Without GEMINI_API_KEY (or if Gemini errors) a labelled local fallback answers via the same tools.
```
Frontend is a single static `frontend/index.html` (vanilla JS, no build step, no secrets). FastAPI serves it at `/`; it can also be hosted elsewhere by setting `window.API_BASE`.

## Folder structure
```
backend/app: main.py (API) engine.py (predictions, impact, alerts, KPIs) ml.py whatif.py optimizer.py sim.py ai.py store.py seed.py domain.py
backend/tests/test_core.py   frontend/index.html   .env.example   .gitignore
```

## Setup and run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env          # optional: fill in keys
uvicorn app.main:app --port 8000    # first start trains models (~5 s) and seeds data
# open http://localhost:8000
```
Seeding is automatic on first start (`seed=7`, reproducible). Reset any time with the "Reset data" button or `curl -X POST localhost:8000/api/admin/reseed`.
Export env vars before starting (`export $(grep -v '^#' ../.env | xargs)`), or set them in your host.

**Firebase:** create a Realtime Database, create a service account, and set `FIREBASE_DATABASE_URL`, `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY` (keep `\n` escapes). On first start the seed is pushed to the paths `/aircraft /components /sensor_readings /maintenance_records /predictions /spares /technicians /bays /maintenance_tasks /maintenance_plans /alerts /simulation /system_config`. Writes mirror only the changed paths. Check `GET /api/health` for `store` and `firebase_error`.
**Gemini:** get a key from Google AI Studio and set `GEMINI_API_KEY`. The header badge shows which copilot engine is active.

## Tests
```bash
cd backend && python -m pytest -q tests
```

## Demo workflow (A17)
1. Command Center: A17 is rank #1, CRITICAL. Click its row.
2. Digital Twin: hydraulic pump shows probability, RUL range, anomaly, risk drivers, telemetry and health trend.
3. Toggle **Live simulation** (A17 / hydraulic_pump) and watch health, RUL, rank and alerts move.
4. What-If: compare repair now, defer 6/12/24 h, bundle. The recommendation and reasons are computed.
5. Optimizer: Optimize plan, review BEFORE vs AFTER, Gantt, reasons; Apply plan to reserve spares.
6. Ask VAYU-NETRA: "Why is A17 high priority?", "What happens if we delay A17 maintenance by 12 hours?", "Show me the optimized maintenance plan."
7. Log Intelligence: submit the sample note; the validated record is stored and A17's prediction updates.

## Model notes and limitations
- Models are trained at start-up on synthetic degradation data. P(fail) is within 50 h; scenario risk assumes constant hazard derived from it. Confidence is a heuristic, not calibrated.
- Risk drivers use occlusion (reset one feature to healthy baseline), not SHAP. XGBoost was not used; scikit-learn GradientBoosting is.
- Fleet impact, downtime penalty (1.5 x repair + 12 h) and bundle factor (0.55) are transparent assumptions in `domain.py`/`whatif.py`.
- "Fleet availability" on the dashboard = (ready + degraded) / total. Projected availability over 72 h is computed from planned plus expected unplanned downtime.
- Live simulation is driven by the browser calling `/api/simulate/telemetry` every 2 s (no WebSocket).
- No authentication on the API. Add Firebase Auth / API gateway before any shared deployment.

## Deployment notes
Backend: any container host (uvicorn, 1 worker since state is cached in-process). Frontend: any static host with `API_BASE` set and `CORS_ORIGINS` configured on the backend.
