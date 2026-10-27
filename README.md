# Wind Forecast Monitor

Day-ahead wind forecast monitor for a UK energy utility buying power one day ahead. For **January 2026** purchase decisions it answers: (1) *what is the latest wind forecast available at decision time?* and (2) *how wrong has that forecast been?* Data: Elexon BMRS only: FUELHH (`fuelType=WIND`) actuals and WINDFOR forecasts, national level.

> **Verification status (read first).** Built in an offline sandbox. What was actually run: the pandas decision-time, metrics and normalisation logic (8 unit tests, all passing; run with a small stub runner because `pytest`/`httpx` could not be installed offline). **Not run:** the Elexon HTTP client against the live API, FastAPI, `npm install`/TypeScript build, Docker, deployment. Elexon request parameters and window limits were written from knowledge of the API, not verified against the docs. Complete the first-run checklist below before relying on it.

- **Live URLs:** frontend `https://<your-app>.vercel.app` (placeholder) · backend `https://<your-api>.onrender.com` (placeholder; OpenAPI at `/docs`)
- **Theme:** reint.ai could not be fetched offline. `frontend/src/theme.css` is a dark, green/cyan energy-tech approximation using CSS variables; adjust the tokens to match the real site. Wordmark is a neutral placeholder.
- **AI tools used:** this project was designed and written with AI assistance (Claude, by Anthropic). Review code and numbers before use.

## First-run checklist
1. Open the Elexon docs for [FUELHH stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) and [WINDFOR stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream). Confirm the parameter names (`publishDateTimeFrom/To`, `fuelType`), response shape (array of objects with `startTime`, `publishTime`, `generation`) and max window; adjust `ACTUALS_CHUNK_DAYS` / `FORECAST_CHUNK_DAYS` (`backend/app/config.py`, env vars) and `services/elexon.py` if they differ.
2. Run the backend and open `/docs`; call `/api/decision-forecast?start=2026-01-15`.
3. Run the frontend and confirm January data renders.

## Run
```bash
docker compose up --build         # UI http://localhost:3000 · API http://localhost:8000/docs
# without Docker
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev      # http://localhost:5173 (proxies /api to :8000)
cd backend && pytest                            # unit tests
```
The first request downloads January data from Elexon (can take a minute); responses are cached on disk (`CACHE_DIR`).

## API
`GET /api/health` · `/api/actuals` · `/api/forecasts` (optional `publish_cutoff`) · `/api/decision-forecast` (`start,end,cutoff=HH:MM,horizon_min,horizon_max`) · `/api/metrics` (same + `buffer_percentile`). Dates must be within 2026-01-01..31.

## Assumptions
Decision cutoff: delivery day D is bought on D-1; default **09:00 UTC on D-1**, configurable in the UI/API (`DEFAULT_CUTOFF_UTC`). Reasoning: leaves time to act before a typical midday day-ahead gate closure while using the morning forecast update. This is an assumption, not a client-confirmed rule.
Latest available forecast: per target `startTime`, the row with the greatest `publishTime <= cutoff`. Nothing published later is ever used (tested).
UTC everywhere, labelled in the UI; no local-time/DST conversion (no DST change in January anyway).
Missing data: slots with no eligible forecast stay in the table as empty and are counted; slots with no actual keep the forecast but are excluded from error metrics; non-numeric generation is dropped; duplicate `(startTime, publishTime)` and duplicate actuals keep the last row.
Horizon filter is applied after selection (it filters rows; it does not change which forecast is selected).
Hourly comparison: WINDFOR publishes one forecast per hour, so forecast and actual are compared on the 24 hourly slots per day (actuals are taken at the same on-the-hour timestamps). Half-hourly actuals are not interpolated against.”

## Metrics (error = forecast − actual; positive = wind over-forecast)
MAE = mean|e| · RMSE = sqrt(mean e²) · Bias = mean e · MAPE = mean(|e|/|actual|)·100 over slots with |actual| > 1 MW · percentiles P50/P90/P95/P99 of |e|. Horizon = startTime − publishTime in hours (6h bins).
**Buffer (indicative):** P-th percentile (default 90) of max(e, 0); conservative wind = max(forecast − buffer, 0). One month of data; not a guarantee.

## Deploy
- **Backend (Render):** push repo, New → Blueprint, select `render.yaml`; set `CORS_ORIGINS` to the Vercel URL. (Alternative: `backend/Procfile` for Heroku.) Render free-tier disk is ephemeral, so the cache refills after restarts.
- **Frontend (Vercel):** import repo, root directory `frontend`, env `VITE_API_URL=https://<your-api>.onrender.com`, deploy. Then put both URLs above.

## Known limitations
No auth, no tests for the HTTP client or UI, file cache only, January 2026 only, national wind only.
