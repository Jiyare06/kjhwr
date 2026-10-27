from datetime import date, time

import numpy as np
import pandas as pd

from app.services import elexon, metrics
from app.services.decision import add_horizon, cutoff_for, decision_table, select_latest

T = lambda s: pd.Timestamp(s, tz="UTC")


def fc(rows):
    return pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"]).assign(
        startTime=lambda d: d.startTime.map(T), publishTime=lambda d: d.publishTime.map(T))


def test_cutoff_is_previous_day():
    assert cutoff_for(date(2026, 1, 10), time(9)) == T("2026-01-09 09:00")


def test_select_latest_not_after_cutoff():
    f = fc([("2026-01-10 12:00", "2026-01-08 06:00", 100),
            ("2026-01-10 12:00", "2026-01-09 08:00", 200),
            ("2026-01-10 12:00", "2026-01-09 09:00", 300),   # == cutoff, allowed
            ("2026-01-10 12:00", "2026-01-09 09:01", 999)])  # after cutoff, never used
    out = select_latest(f, T("2026-01-09 09:00"))
    assert out.generation.tolist() == [300]


def test_no_leakage_property():
    rng = np.random.default_rng(0)
    base = T("2026-01-08")
    rows = [("2026-01-10 00:00", base + pd.Timedelta(minutes=int(m)), float(i))
            for i, m in enumerate(rng.integers(0, 3000, 200))]
    f = fc([(a, str(b), c) for a, b, c in rows])
    cutoff = T("2026-01-09 09:00")
    out = select_latest(f, cutoff)
    assert (out.publishTime <= cutoff).all()


def test_missing_forecast_leaves_nan_and_unavailable_after_cutoff():
    f = fc([("2026-01-10 00:00", "2026-01-09 10:00", 5)])  # published after cutoff
    a = pd.DataFrame({"startTime": [T("2026-01-10 00:00")], "actual": [4.0]})
    t = decision_table(f, a, date(2026, 1, 10), date(2026, 1, 10), time(9))
    assert len(t) == 24 and t.forecast.isna().all()


def test_horizon():
    d = add_horizon(fc([("2026-01-10 12:00", "2026-01-09 09:00", 1)]))
    assert d.horizon_h.iloc[0] == 27.0


def test_metrics_values_and_mape_guard():
    df = pd.DataFrame({"forecast": [110.0, 90.0, 5.0], "actual": [100.0, 100.0, 0.0]})
    df["error"] = df.forecast - df.actual
    s = metrics.summarise(df)
    assert s["mae"] == (10 + 10 + 5) / 3
    assert round(s["bias"], 6) == round((10 - 10 + 5) / 3, 6)
    assert round(s["rmse"], 6) == round(np.sqrt((100 + 100 + 25) / 3), 6)
    assert s["mape"] == 10.0  # zero actual skipped


def test_buffer_floors_at_zero():
    df = pd.DataFrame({"forecast": [100.0] * 4, "actual": [150.0] * 4})
    df["error"] = df.forecast - df.actual  # always under-forecast -> no shortfall risk
    assert metrics.buffer_recommendation(df)["buffer_mw"] == 0


def test_duplicates_and_chunks():
    rows = [{"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T09:00:00Z", "generation": 1},
            {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T09:00:00Z", "generation": 2}]
    assert len(elexon.normalise_forecasts(rows)) == 1
    w = elexon.chunk_windows(T("2026-01-01").to_pydatetime(), T("2026-01-09").to_pydatetime(), 3)
    assert len(w) == 3 and w[0][1] == w[1][0] and w[-1][1] == T("2026-01-09")
