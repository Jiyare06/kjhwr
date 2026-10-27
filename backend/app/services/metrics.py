"""Error metrics. error = forecast - actual (positive = wind over-forecast = shortfall risk)."""
import numpy as np
import pandas as pd

PCTS = (50, 90, 95, 99)


def summarise(df: pd.DataFrame, zero_eps: float = 1.0) -> dict:
    d = df.dropna(subset=["error"])
    n = len(d)
    if n == 0:
        return {"n": 0}
    e, a = d["error"].to_numpy(), d["actual"].to_numpy()
    mask = np.abs(a) > zero_eps  # MAPE guard: skip near-zero actuals
    mape = float(np.mean(np.abs(e[mask] / a[mask])) * 100) if mask.any() else None
    abs_e = np.abs(e)
    over = np.clip(e, 0, None)
    return {
        "n": n,
        "mae": float(abs_e.mean()),
        "rmse": float(np.sqrt((e**2).mean())),
        "bias": float(e.mean()),
        "mape": mape,
        "abs_error_pct": {f"p{p}": float(np.percentile(abs_e, p)) for p in PCTS},
        "over_forecast_pct": {f"p{p}": float(np.percentile(over, p)) for p in PCTS},
        "mean_actual": float(a.mean()),
    }


def group_metrics(df: pd.DataFrame, key: pd.Series, label: str) -> list[dict]:
    d = df.dropna(subset=["error"]).assign(**{label: key})
    out = []
    for k, g in d.groupby(label, observed=True):
        s = summarise(g)
        out.append({label: k if not hasattr(k, "item") else k.item(),
                    "n": s["n"], "mae": s["mae"], "rmse": s["rmse"], "bias": s["bias"]})
    return out


def histogram(df: pd.DataFrame, bins: int = 30) -> list[dict]:
    e = df["error"].dropna().to_numpy()
    if len(e) == 0:
        return []
    counts, edges = np.histogram(e, bins=bins)
    return [{"from": float(edges[i]), "to": float(edges[i + 1]), "count": int(c)}
            for i, c in enumerate(counts)]


def horizon_bins(df: pd.DataFrame, width_h: int = 6) -> pd.Series:
    b = (df["horizon_h"] // width_h * width_h).astype("Int64")
    return b.map(lambda x: None if pd.isna(x) else f"{x}-{x + width_h}h")


def buffer_recommendation(df: pd.DataFrame, q: float = 90) -> dict:
    """Indicative: conservative wind = forecast - P{q} over-forecast error (floored at 0)."""
    d = df.dropna(subset=["error", "forecast"])
    if d.empty:
        return {"q": q, "buffer_mw": None}
    e, f = d["error"].to_numpy(), d["forecast"].to_numpy()
    buf = float(np.percentile(np.clip(e, 0, None), q))
    # Bias-aware view (added fields only): remove the average over-forecast first, then size a
    # P{q} buffer on what is left. Bias and buffer are estimated on the same month (in-sample).
    bias = float(e.mean())
    resid_buf = float(np.percentile(np.clip(e - bias, 0, None), q))
    return {"q": q, "buffer_mw": buf,
            "mean_forecast": float(f.mean()),
            "mean_conservative_wind": float(np.clip(f - buf, 0, None).mean()),
            "bias_mw": bias,
            "mean_bias_corrected_forecast": float(np.clip(f - bias, 0, None).mean()),
            "residual_buffer_mw": resid_buf,
            "mean_conservative_wind_bias_aware": float(np.clip(f - bias - resid_buf, 0, None).mean()),
            "note": "Indicative only: empirical percentile of January 2026 errors; not a guarantee."}


def cutoff_comparison(tables: dict[str, pd.DataFrame]) -> list[dict]:
    """Headline error metrics for the same slots under different decision cutoffs."""
    out = []
    for cutoff, df in tables.items():
        s = summarise(df.dropna(subset=["error"]))
        row = {"cutoff": cutoff, "n": s["n"]}
        if s["n"]:
            row.update(mae=s["mae"], rmse=s["rmse"], bias=s["bias"], p90_abs=s["abs_error_pct"]["p90"],
                       mean_horizon_h=float(df["horizon_h"].mean()))
        out.append(row)
    return out
