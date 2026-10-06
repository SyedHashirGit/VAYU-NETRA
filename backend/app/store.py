"""Data store: Firebase Realtime Database (via Admin SDK) when configured, else local JSON file.
Writes always go through commit(); both backends hold the same path layout."""
import json, os, threading
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

ROOTS = ["aircraft", "components", "sensor_readings", "maintenance_records", "predictions", "spares",
         "technicians", "bays", "maintenance_tasks", "maintenance_plans", "alerts", "simulation", "system_config"]

class Store:
    def __init__(self):
        self.lock = threading.RLock()
        self.data = {r: {} for r in ROOTS}
        self.fb = None
        self.fb_error = None
        if os.getenv("VERCEL"):
            d = Path("/tmp/data")
        else:
            d = Path(os.getenv("AERO_DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
        d.mkdir(parents=True, exist_ok=True)
        self.path = d / "db.json"
        self._init_firebase()

    @property
    def backend(self):
        return "firebase-realtime-db" if self.fb else "local-json"

    def _init_firebase(self):
        url = os.getenv("FIREBASE_DATABASE_URL")
        key = os.getenv("FIREBASE_PRIVATE_KEY")
        if not url:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials, db
            if key:
                cred = credentials.Certificate({
                    "type": "service_account", "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"), "private_key": key.replace("\\n", "\n"),
                    "token_uri": "https://oauth2.googleapis.com/token"})
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred, {"databaseURL": url})
            else:
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(options={"databaseURL": url})
            self.fb = db
        except Exception as e:  # keep running on local JSON
            self.fb_error = str(e)

    def load(self):
        """Returns True if existing data was loaded."""
        try:
            if self.fb:
                loaded = {r: (self.fb.reference("/" + r).get() or {}) for r in ROOTS}
            elif self.path.exists():
                loaded = json.loads(self.path.read_text())
            else:
                return False
            if not loaded.get("aircraft"):
                return False
            self.data = {r: loaded.get(r, {}) for r in ROOTS}
            return True
        except Exception as e:
            self.fb_error = str(e)
            self.fb = None
            return False

    def get(self, path, default=None):
        cur = self.data
        for k in path.strip("/").split("/"):
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def commit(self, *paths):
        """Persist the whole local copy; mirror only the given paths to Firebase."""
        with self.lock:
            try:
                self.path.write_text(json.dumps(self.data))
            except OSError as e:
                self.fb_error = f"local write failed: {e}"
            if self.fb:
                for p in (paths or ROOTS):
                    try:
                        self.fb.reference("/" + p.strip("/")).set(self.get(p, {}))
                    except Exception as e:
                        self.fb_error = f"firebase write failed on {p}: {e}"


S = Store()
