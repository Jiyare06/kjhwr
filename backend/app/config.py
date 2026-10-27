import os
from datetime import date, time

JAN_START = date(2026, 1, 1)
JAN_END = date(2026, 1, 31)
DEFAULT_CUTOFF = time.fromisoformat(os.getenv("DEFAULT_CUTOFF_UTC", "09:00"))  # on D-1
ELEXON_BASE = os.getenv("ELEXON_BASE", "https://data.elexon.co.uk/bmrs/api/v1")
CACHE_DIR = os.getenv("CACHE_DIR", "/tmp/wfm-cache")
# Max window per request. Verified live (Oct 2026): WINDFOR stream returned 123 days of publishes
# and FUELHH 32 days in a single call, so the January window is fetched in one request per dataset.
ACTUALS_CHUNK_DAYS = int(os.getenv("ACTUALS_CHUNK_DAYS", "35"))
FORECAST_CHUNK_DAYS = int(os.getenv("FORECAST_CHUNK_DAYS", "40"))
# Forecasts published this many days before the first delivery day are loaded (max horizon ~42 h).
FORECAST_LOOKBACK_DAYS = 3
# Extra cutoffs compared on the Accuracy view (all before the 09:50 GMT N2EX gate closure).
COMPARE_CUTOFFS = os.getenv("COMPARE_CUTOFFS_UTC", "04:30,09:00,09:30").split(",")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
