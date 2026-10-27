from datetime import date, datetime, time, timedelta, timezone

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .services import elexon, metrics
from .services.decision import cutoff_for, decision_table, select_latest

app = FastAPI(title="Wind Forecast Monitor", version="1.0.0",
              description="UK national wind: decision-time forecasts vs Elexon actuals (Jan 2026).")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
UTC = timezone.utc


def _dt(d: date) -> datetime:
    return datetime.combine(d, time(0), tzinfo=UTC)


def _check(start: date, end: date) -> None:
    if not (config.JAN_START <= start <= end <= config.JAN_END):
        raise HTTPException(400, "Dates must satisfy 2026-01-01 <= start <= end <= 2026-01-31")


def _cutoff(cutoff: str | None) -> time:
    try:
        return time.fromisoformat(cutoff) if cutoff else config.DEFAULT_CUTOFF
    except ValueError:
        raise HTTPException(400, "cutoff must be HH:MM (UTC)")


def _records(df: pd.DataFrame) -> list[dict]:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return d.astype(object).where(d.notna(), None).to_dict("records")


async def _month():
    """Whole January window, fetched once per process (one Elexon request per dataset)."""
    lookback = timedelta(days=config.FORECAST_LOOKBACK_DAYS)
    try:
        fc = await elexon.month_forecasts(_dt(config.JAN_START) - lookback, _dt(config.JAN_END))
        ac = await elexon.month_actuals(_dt(config.JAN_START), _dt(config.JAN_END))
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    return fc, ac


def _forecast_window(fc: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Same eligibility window as before: published within [start - lookback, end], for target days."""
    lo = _dt(start) - timedelta(days=config.FORECAST_LOOKBACK_DAYS)
    return fc[(fc.publishTime >= lo) & (fc.publishTime <= _dt(end))
              & (fc.startTime >= _dt(start)) & (fc.startTime < _dt(end) + timedelta(days=1))]


def _filter_horizon(df: pd.DataFrame, hmin, hmax) -> pd.DataFrame:
    if hmin is not None:
        df = df[df["horizon_h"] >= hmin]
    if hmax is not None:
        df = df[df["horizon_h"] <= hmax]
    return df


async def _table(start, end, cutoff, hmin, hmax) -> pd.DataFrame:
    _check(start, end)
    cut = _cutoff(cutoff)
    fc, ac = await _month()
    df = decision_table(_forecast_window(fc, start, end), ac, start, end, cut)
    return _filter_horizon(df, hmin, hmax)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(UTC).isoformat()}


@app.get("/api/actuals")
async def actuals(start: date = Query(config.JAN_START), end: date = Query(config.JAN_END)):
    _check(start, end)
    _, df = await _month()
    df = df[(df.startTime >= _dt(start)) & (df.startTime < _dt(end) + timedelta(days=1))]
    return _records(df)


@app.get("/api/forecasts")
async def forecasts(start: date = Query(config.JAN_START), end: date = Query(config.JAN_END),
                    publish_cutoff: datetime | None = Query(None, description="Only forecasts published <= this (UTC)")):
    _check(start, end)
    fc, _ = await _month()
    df = _forecast_window(fc, start, end)
    if publish_cutoff:
        df = df[df.publishTime <= pd.Timestamp(publish_cutoff, tz=UTC) if publish_cutoff.tzinfo is None
                else df.publishTime <= pd.Timestamp(publish_cutoff)]
    return _records(df)


@app.get("/api/decision-forecast")
async def decision_forecast(start: date = Query(config.JAN_START), end: date | None = None,
                            cutoff: str | None = Query(None, description="HH:MM UTC on D-1"),
                            horizon_min: float | None = None, horizon_max: float | None = None):
    end = end or start
    df = await _table(start, end, cutoff, horizon_min, horizon_max)
    f = df["forecast"].dropna()
    stats = {"mean": f.mean(), "min": f.min(), "max": f.max(), "missing_slots": int(df["forecast"].isna().sum())} \
        if len(f) else {"missing_slots": int(len(df))}
    stats = {k: (None if pd.isna(v) else float(v)) for k, v in stats.items()}
    return {"cutoff_time_utc": _cutoff(cutoff).strftime("%H:%M"), "stats": stats, "rows": _records(df)}


@app.get("/api/metrics")
async def get_metrics(start: date = Query(config.JAN_START), end: date = Query(config.JAN_END),
                      cutoff: str | None = None, horizon_min: float | None = None,
                      horizon_max: float | None = None, buffer_percentile: float = Query(90, ge=50, le=99.9)):
    df = await _table(start, end, cutoff, horizon_min, horizon_max)
    ok = df.dropna(subset=["error"])
    # Same slots scored under a few alternative cutoffs (added field; existing fields unchanged).
    chosen = _cutoff(cutoff).strftime("%H:%M")
    others = sorted({chosen, *(c.strip() for c in config.COMPARE_CUTOFFS if c.strip())})
    compare = {c: (df if c == chosen else await _table(start, end, c, horizon_min, horizon_max))
               for c in others}
    return {
        "cutoff_time_utc": _cutoff(cutoff).strftime("%H:%M"),
        "summary": metrics.summarise(ok),
        "by_hour": metrics.group_metrics(ok, ok["startTime"].dt.hour, "hour"),
        "by_day": metrics.group_metrics(ok, ok["delivery_day"], "day"),
        "by_horizon": metrics.group_metrics(ok, metrics.horizon_bins(ok), "horizon"),
        "histogram": metrics.histogram(ok),
        "buffer": metrics.buffer_recommendation(ok, buffer_percentile),
        "coverage": {"slots": int(len(df)), "with_forecast": int(df["forecast"].notna().sum()),
                     "with_actual": int(df["actual"].notna().sum()), "scored": int(len(ok))},
        "cutoff_comparison": metrics.cutoff_comparison(compare),
    }
