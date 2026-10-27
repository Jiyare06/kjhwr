import os
from datetime import date, time

JAN_START = date(2026, 1, 1)
JAN_END = date(2026, 1, 31)
DEFAULT_CUTOFF = time.fromisoformat(os.getenv("DEFAULT_CUTOFF_UTC", "09:00"))  # on D-1
ELEXON_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
CACHE_DIR = os.getenv("CACHE_DIR", "/tmp/wfm-cache")
# Max window per request. Conservative; verify against the live docs (see README).
ACTUALS_CHUNK_DAYS = int(os.getenv("ACTUALS_CHUNK_DAYS", "7"))
FORECAST_CHUNK_DAYS = int(os.getenv("FORECAST_CHUNK_DAYS", "3"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
