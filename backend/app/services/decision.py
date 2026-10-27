"""Decision-time forecast selection. No look-ahead: publishTime <= cutoff, always."""
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

UTC = timezone.utc


def cutoff_for(day: date, cutoff_time: time) -> pd.Timestamp:
    """Decision is taken on D-1 at `cutoff_time` UTC."""
    return pd.Timestamp(datetime.combine(day - timedelta(days=1), cutoff_time, tzinfo=UTC))


def select_latest(forecasts: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Per startTime, the forecast with the greatest publishTime <= cutoff."""
    eligible = forecasts[forecasts["publishTime"] <= cutoff]
    out = (eligible.sort_values(["startTime", "publishTime"])
           .drop_duplicates("startTime", keep="last"))
    return out.reset_index(drop=True)


def day_slots(day: date) -> pd.DatetimeIndex:
    """24 hourly slots. WINDFOR is hourly (startTime always on :00, verified on January 2026 data),
    so the FUELHH :30 half-hours have no forecast to score against and are not used.
    Forecasts are never interpolated to :30."""
    start = pd.Timestamp(datetime.combine(day, time(0), tzinfo=UTC))
    return pd.date_range(start, periods=24, freq="60min")


def add_horizon(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df


def decision_table(forecasts: pd.DataFrame, actuals: pd.DataFrame, start: date, end: date,
                   cutoff_time: time) -> pd.DataFrame:
    """One row per hourly slot over [start, end] using the D-1 cutoff forecast, joined to actuals."""
    parts = []
    d = start
    while d <= end:
        sel = select_latest(forecasts, cutoff_for(d, cutoff_time))
        slots = pd.DataFrame({"startTime": day_slots(d)})
        part = slots.merge(sel, on="startTime", how="left")  # missing forecast -> NaN, kept visible
        part["delivery_day"] = d.isoformat()
        part["cutoff"] = cutoff_for(d, cutoff_time)
        parts.append(part)
        d += timedelta(days=1)
    df = pd.concat(parts, ignore_index=True).rename(columns={"generation": "forecast"})
    df = df.merge(actuals, on="startTime", how="left")
    df = add_horizon(df)
    df["error"] = df["forecast"] - df["actual"]
    return df
