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


def test_half_hour_actuals_not_scored_against_hourly_forecasts():
    f = fc([("2026-01-10 00:00", "2026-01-09 07:30", 100)])
    a = pd.DataFrame({"startTime": [T("2026-01-10 00:00"), T("2026-01-10 00:30")], "actual": [90.0, 80.0]})
    t = decision_table(f, a, date(2026, 1, 10), date(2026, 1, 10), time(9))
    assert len(t) == 24 and t.error.dropna().tolist() == [10.0]


def test_bias_aware_buffer_fields():
    df = pd.DataFrame({"forecast": [110.0, 120.0, 130.0, 140.0], "actual": [100.0] * 4})
    df["error"] = df.forecast - df.actual  # 10, 20, 30, 40 -> bias 25
    b = metrics.buffer_recommendation(df, 90)
    assert b["bias_mw"] == 25
    assert b["mean_bias_corrected_forecast"] == 100
    assert b["residual_buffer_mw"] == float(np.percentile([0, 0, 5, 15], 90))
    assert b["buffer_mw"] == float(np.percentile([10, 20, 30, 40], 90))  # existing field unchanged


def test_cutoff_comparison_uses_only_forecasts_before_each_cutoff():
    f = fc([("2026-01-10 12:00", "2026-01-09 07:30", 120),
            ("2026-01-10 12:00", "2026-01-09 09:30", 105)])
    a = pd.DataFrame({"startTime": [T("2026-01-10 12:00")], "actual": [100.0]})
    tabs = {c: decision_table(f, a, date(2026, 1, 10), date(2026, 1, 10), time.fromisoformat(c))
            for c in ("09:00", "09:30")}
    rows = {r["cutoff"]: r for r in metrics.cutoff_comparison(tabs)}
    assert rows["09:00"]["mae"] == 20 and rows["09:30"]["mae"] == 5


def test_month_data_fetched_once(monkeypatch):
    import asyncio
    calls = []

    async def fake_fetch(path, start, end, days, extra):
        calls.append(path)
        return []

    monkeypatch.setattr(elexon, "_fetch", fake_fetch)
    elexon._memo.clear()
    s, e = T("2025-12-29").to_pydatetime(), T("2026-01-31").to_pydatetime()

    async def run():
        await asyncio.gather(*(elexon.month_forecasts(s, e) for _ in range(5)))
        await elexon.month_actuals(s, e)

    asyncio.run(run())
    elexon._memo.clear()
    assert calls == ["/datasets/WINDFOR/stream", "/datasets/FUELHH/stream"]


def test_single_request_per_dataset_for_january():
    from app import config
    assert len(elexon.chunk_windows(T("2025-12-29").to_pydatetime(), T("2026-01-31").to_pydatetime(),
                                    config.FORECAST_CHUNK_DAYS)) == 1
    assert len(elexon.chunk_windows(T("2026-01-01").to_pydatetime(), T("2026-02-01").to_pydatetime(),
                                    config.ACTUALS_CHUNK_DAYS)) == 1
