const BASE = (import.meta.env.VITE_API_URL ?? "") as string;

export interface Row { startTime: string; publishTime: string | null; forecast: number | null; actual: number | null;
  horizon_h: number | null; error: number | null; delivery_day: string; }
export interface Params { start: string; end: string; cutoff: string; horizonMin?: string; horizonMax?: string; }
export interface Group { n: number; mae: number; rmse: number; bias: number; hour?: number; day?: string; horizon?: string; }
export interface Metrics {
  summary: { n: number; mae?: number; rmse?: number; bias?: number; mape?: number | null;
    abs_error_pct?: Record<string, number>; over_forecast_pct?: Record<string, number> };
  by_hour: Group[]; by_day: Group[]; by_horizon: Group[];
  histogram: { from: number; to: number; count: number }[];
  buffer: { q: number; buffer_mw: number | null; mean_forecast?: number; mean_conservative_wind?: number; note?: string };
  coverage: { slots: number; with_forecast: number; with_actual: number; scored: number };
}

function qs(p: Params, extra: Record<string, string> = {}) {
  const q = new URLSearchParams({ start: p.start, end: p.end, cutoff: p.cutoff, ...extra });
  if (p.horizonMin) q.set("horizon_min", p.horizonMin);
  if (p.horizonMax) q.set("horizon_max", p.horizonMax);
  return q.toString();
}
async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `Request failed (${r.status})`);
  return r.json();
}
export const fetchDecision = (p: Params) =>
  get<{ stats: Record<string, number | null>; rows: Row[] }>(`/api/decision-forecast?${qs(p)}`);
export const fetchMetrics = (p: Params, bp: number) => get<Metrics>(`/api/metrics?${qs(p, { buffer_percentile: String(bp) })}`);
