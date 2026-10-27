# Wind Forecast Monitor

Day-ahead wind forecast monitor for a UK energy utility that buys power one day ahead. For **January 2026** purchase decisions it answers two questions: (1) *what was the latest wind forecast available when the purchase decision had to be made?* and (2) *how wrong has that forecast been, in MW?* Data: Elexon BMRS only, national level: FUELHH actuals (`fuelType=WIND`) and WINDFOR forecasts.

- **Live app:** https://wind-forecast-monitor-gamma.vercel.app
- **Live API:** https://wind-forecast-monitor-le2l.onrender.com (OpenAPI docs at `/docs`, health at `/api/health`). Render's free tier sleeps when idle, so the first request after a pause can take up to a minute.
- **AI tools used:** this project was designed and written with AI assistance (Claude, by Anthropic), including code, tests and documentation. All numbers in the docs come from the running app.

## January 2026 at a glance (default 09:00 UTC cutoff)
| Metric | Value |
|---|---|
| Hourly slots scored | 744 of 744 (no missing forecasts or actuals) |
| MAE | 2,127.5 MW |
| RMSE | 2,606.1 MW |
| Bias (forecast − actual) | +1,851.5 MW (forecast too high in 631 of 744 hours) |
| MAPE | 22.2 % |
| \|Error\| P50 / P90 / P95 / P99 | 1,758.5 / 4,306.4 / 5,350.9 / 6,139.5 MW |
| Mean actual wind | 11,581 MW |

## Run
```bash
docker compose up --build         # UI http://localhost:3000 · API http://localhost:8000/docs
# without Docker
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev      # http://localhost:5173 (proxies /api to :8000)
cd backend && pytest                            # unit tests
```
The first request downloads the January window from Elexon (one request per dataset) and caches it in memory and on disk (`CACHE_DIR`); later requests reuse it.

## API
`GET /api/health` · `/api/actuals` · `/api/forecasts` (optional `publish_cutoff`) · `/api/decision-forecast` (`start,end,cutoff=HH:MM,horizon_min,horizon_max`) · `/api/metrics` (same + `buffer_percentile`; also returns `cutoff_comparison` and bias-aware buffer fields). Dates must be within 2026-01-01..31.

## Decision cutoff
Delivery day D is bought on D-1. The default cutoff is **09:00 UTC on D-1**, configurable in the UI, the API (`cutoff`) and the environment (`DEFAULT_CUTOFF_UTC`).

Why 09:00:
- The GB day-ahead auction (Nord Pool N2EX) closes at **09:50 GMT** on D-1 ([Nord Pool](https://support.nordpoolgroup.com/support/solutions/articles/8000088463-about-the-day-ahead-gb-auction)). January has no daylight saving, so GMT = UTC.
- WINDFOR runs are published at about 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC (checked on January 2026 data). At 09:00 the latest run is the 07:30 one.
- Waiting for the 09:30 run leaves only 20 minutes before gate closure and barely changes accuracy: MAE 2,107.2 vs 2,127.5 MW, while RMSE (2,611.2 vs 2,606.1 MW) and P90 (4,377.0 vs 4,306.4 MW) get slightly worse. 09:00 leaves time to act at almost no accuracy cost. The Accuracy tab shows this comparison for 04:30, 09:00 and 09:30.

This is still an assumption to confirm with the client's trading desk.

**No look-ahead:** for each target `startTime`, the forecast used is the row with the greatest `publishTime <= cutoff`. Nothing published after the cutoff is ever used (tested, including the equal-to-cutoff boundary).

## Assumptions
- UTC everywhere, labelled in the UI.
- **Hourly comparison.** WINDFOR only forecasts on-the-hour start times. FUELHH is half-hourly, so forecasts are scored against the 24 on-the-hour actuals per day. The :30 actuals have no forecast to compare against and are not used. Forecasts are not interpolated.
- **Missing data.** Slots with no eligible forecast stay visible as empty and are counted. Slots with no actual keep the forecast but are excluded from error metrics. Non-numeric generation is dropped. Duplicate `(startTime, publishTime)` rows and duplicate actuals keep the last row.
- **Horizon filter** is applied after selection: it filters rows and never changes which forecast is selected.

## Metrics (error = forecast − actual; positive = wind over-forecast = shortfall risk)
- **MAE** = mean|e|
- **RMSE** = sqrt(mean e²)
- **Bias** = mean e
- **MAPE** = mean(|e| / |actual|) × 100, over slots with |actual| > 1 MW
- **Percentiles** P50/P90/P95/P99 of |e|
- **Horizon** = startTime − publishTime in hours, grouped into 6 h bins

**Buffer (indicative):** P-th percentile (default 90) of max(e, 0); conservative wind = max(forecast − buffer, 0).

**Bias-aware view:** the same buffer split into the average over-forecast (bias) and a P-th percentile of what is left, max(e − bias, 0). In January the 4,306 MW P90 buffer is 1,852 MW of systematic over-forecast plus 2,455 MW for variability. Both parts are estimated on the same month (in-sample). Treat them as indicative, not as a guarantee.

## Deploy
- **Backend (Render):** New → Blueprint, select `render.yaml`. Set `CORS_ORIGINS` to the Vercel URL (or `*`). `backend/Procfile` is provided as a Heroku alternative. Render's free-tier disk is ephemeral, so the cache refills after a restart.
- **Frontend (Vercel):** import the repo with root directory `frontend` and set env `VITE_API_URL=https://wind-forecast-monitor-le2l.onrender.com`.
- Deploy the backend first. The frontend tolerates an older backend: the new sections simply don't appear.

## Known limitations
- One month of data only (January 2026), national wind only.
- The cause of the forecast bias is not verified (see `docs/TECH_REVIEW.md`).
- No auth. File and in-memory cache only, not shared across instances.
- No UI tests. The HTTP client is tested with a mocked fetch only.
