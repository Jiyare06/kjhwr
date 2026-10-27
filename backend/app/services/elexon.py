"""Fetch + cache Elexon BMRS streams (FUELHH actuals, WINDFOR forecasts)."""
import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd

from ..config import ACTUALS_CHUNK_DAYS, CACHE_DIR, ELEXON_BASE, FORECAST_CHUNK_DAYS

UTC = timezone.utc


def chunk_windows(start: datetime, end: datetime, days: int) -> list[tuple[datetime, datetime]]:
    out, cur = [], start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        out.append((cur, nxt))
        cur = nxt
    return out


def _fmt(d: datetime) -> str:
    return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _get_json(client: httpx.AsyncClient, path: str, params: dict, retries: int = 4) -> list[dict]:
    key = hashlib.sha1(f"{path}{sorted(params.items())}".encode()).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = await client.get(f"{ELEXON_BASE}{path}", params=params, timeout=60)
            r.raise_for_status()
            body = r.json()
            data = body["data"] if isinstance(body, dict) else body
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(data, f)
            return data
        except (httpx.HTTPError, ValueError, KeyError) as e:
            last = e
            await asyncio.sleep(2**attempt)
    raise RuntimeError(f"Elexon request failed after {retries} attempts: {last}")


async def _fetch(path: str, start: datetime, end: datetime, days: int, extra: dict) -> list[dict]:
    async with httpx.AsyncClient() as client:
        results = []
        for a, b in chunk_windows(start, end, days):
            params = {"publishDateTimeFrom": _fmt(a), "publishDateTimeTo": _fmt(b), **extra}
            results += await _get_json(client, path, params)
        return results


async def load_actuals(start: datetime, end: datetime) -> pd.DataFrame:
    """WIND actuals indexed by 30-min startTime (UTC). Latest publishTime wins on duplicates."""
    rows = await _fetch("/datasets/FUELHH/stream", start, end + timedelta(days=1),
                        ACTUALS_CHUNK_DAYS, {"fuelType": "WIND"})
    return normalise_actuals(rows)


async def load_forecasts(start: datetime, end: datetime) -> pd.DataFrame:
    rows = await _fetch("/datasets/WINDFOR/stream", start, end, FORECAST_CHUNK_DAYS, {})
    return normalise_forecasts(rows)


# In-process memo: every API request reuses one fetch of the fixed January window instead of
# issuing its own date-specific Elexon calls (which also defeated the disk cache).
_memo: dict[str, pd.DataFrame] = {}
_lock = asyncio.Lock()


async def _memoised(name: str, loader) -> pd.DataFrame:
    if name in _memo:
        return _memo[name]
    async with _lock:  # concurrent first requests share one download
        if name not in _memo:
            _memo[name] = await loader()
    return _memo[name]


async def month_forecasts(start: datetime, end: datetime) -> pd.DataFrame:
    """All forecasts for the fixed window [start, end] (publishTime), fetched once per process."""
    return await _memoised("forecasts", lambda: load_forecasts(start, end))


async def month_actuals(start: datetime, end: datetime) -> pd.DataFrame:
    """All WIND actuals for the fixed window, fetched once per process."""
    return await _memoised("actuals", lambda: load_actuals(start, end))


def normalise_actuals(rows: list[dict]) -> pd.DataFrame:
    cols = ["startTime", "actual"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    df = df[df.get("fuelType", "WIND") == "WIND"] if "fuelType" in df else df
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df.get("publishTime", df["startTime"]), utc=True)
    df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    df = df.dropna(subset=["generation"]).sort_values(["startTime", "publishTime"])
    df = df.drop_duplicates("startTime", keep="last")
    return df.rename(columns={"generation": "actual"})[cols].reset_index(drop=True)


def normalise_forecasts(rows: list[dict]) -> pd.DataFrame:
    cols = ["startTime", "publishTime", "generation"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    df = df.dropna(subset=["generation"])
    df = df.drop_duplicates(["startTime", "publishTime"], keep="last")
    return df[cols].sort_values(["startTime", "publishTime"]).reset_index(drop=True)
