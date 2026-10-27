import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Metrics, Row } from "../api";
import { axisMW, fmtDay, fmtMW, fmtTime, tipStyle } from "../format";
import { Card, Empty, Kpi } from "./Ui";

const Bars = ({ data, x, tick }: { data: any[]; x: string; tick?: (v: any) => string }) =>
  <ResponsiveContainer width="100%" height={260}><BarChart data={data}><CartesianGrid stroke="#1f3a34" />
    <XAxis dataKey={x} stroke="#8fa9a1" tickFormatter={tick} /><YAxis stroke="#8fa9a1" tickFormatter={axisMW} width={70} />
    <Tooltip contentStyle={tipStyle} labelFormatter={(l) => (tick ? tick(l) : String(l))} formatter={(v) => fmtMW(v)} /><Legend />
    <Bar dataKey="mae" name="MAE" fill="#3ddc97" /><Bar dataKey="rmse" name="RMSE" fill="#4cc9f0" /><Bar dataKey="bias" name="Bias" fill="#ffb454" /></BarChart></ResponsiveContainer>;

const hourTick = (h: any) => `${String(h).padStart(2, "0")}:00`;

export function AccuracyView({ m, rows, bp, setBp }: { m: Metrics; rows: Row[]; bp: number; setBp: (n: number) => void }) {
  const s = m.summary;
  if (!s.n) return <Empty />;
  const hist = m.histogram.map(h => ({ bin: Math.round((h.from + h.to) / 2), count: h.count }));
  const hz = [...m.by_horizon].sort((a, b) => parseInt(a.horizon!) - parseInt(b.horizon!));
  const b = m.buffer;
  const bias = s.bias ?? 0;
  const days = m.by_day.length;
  const period = days ? `${fmtDay(m.by_day[0].day!)} – ${fmtDay(m.by_day[days - 1].day!)} 2026` : "the selected period";
  return <>
    <div className="callout bias">
      Forecasts ran {bias >= 0 ? "higher" : "lower"} than actuals on average in {period} by <b>{fmtMW(Math.abs(bias))}</b>
      {" "}(mean actual {fmtMW(s.mean_actual)}). Treat the raw forecast as {bias >= 0 ? "optimistic" : "pessimistic"} when sizing purchases.
    </div>
    <div className="kpis">
      <Kpi label="MAE" value={s.mae} unit="MW" /><Kpi label="RMSE" value={s.rmse} unit="MW" /><Kpi label="Bias (forecast − actual)" value={s.bias} unit="MW" />
      <Kpi label="MAPE" value={s.mape} unit="%" /><Kpi label="Slots scored" value={s.n} />
      {["p50", "p90", "p95", "p99"].map(k => <Kpi key={k} label={`|Error| ${k.toUpperCase()}`} value={s.abs_error_pct?.[k]} unit="MW" />)}
    </div>
    <Card title="Buffer recommendation (indicative)" hint="Conservative wind = forecast − P-th percentile of historical over-forecast error (floored at 0).">
      <label style={{ maxWidth: 240 }}>Confidence percentile: P{bp}
        <input type="range" min={50} max={99} value={bp} onChange={e => setBp(+e.target.value)} /></label>
      <div className="kpis" style={{ marginTop: 12 }}>
        <Kpi label="Extra power to procure (buffer)" value={b.buffer_mw} unit="MW" />
        <Kpi label="Mean forecast wind" value={b.mean_forecast} unit="MW" />
        <Kpi label="Mean conservative wind" value={b.mean_conservative_wind} unit="MW" /></div>
      {b.bias_mw != null && <>
        <h4 className="sub-h">Bias-aware view</h4>
        <p className="hint">Splits the buffer into the average over-forecast (systematic) and a P{bp} allowance for the remaining
          variability. Bias and percentile are both estimated from the same period, so this is in-sample.</p>
        <div className="kpis">
          <Kpi label="Systematic over-forecast (bias)" value={b.bias_mw} unit="MW" />
          <Kpi label={`P${bp} under-delivery buffer after bias`} value={b.residual_buffer_mw} unit="MW" />
          <Kpi label="Mean bias-corrected forecast" value={b.mean_bias_corrected_forecast} unit="MW" />
          <Kpi label="Mean conservative wind (bias-aware)" value={b.mean_conservative_wind_bias_aware} unit="MW" /></div>
      </>}
      <div className="callout">Indicative only. Based on one month of errors; assumes January 2026 is representative. Not a guarantee of cover.</div>
    </Card>
    {m.cutoff_comparison && m.cutoff_comparison.length > 1 &&
      <Card title="Effect of the decision cutoff" hint="Same delivery slots and filters, scored with the latest forecast available at each D-1 cutoff (UTC). All cutoffs are before the 09:50 GMT day-ahead auction gate closure. WINDFOR publishes around 02:30, 04:30, 07:30 and 09:30 each morning.">
        <div className="table-wrap"><table>
          <thead><tr><th>Cutoff (D-1)</th><th>Avg lead time</th><th>MAE</th><th>RMSE</th><th>Bias</th><th>|Error| P90</th></tr></thead>
          <tbody>{m.cutoff_comparison.map(r => <tr key={r.cutoff} className={r.cutoff === m.cutoff_time_utc ? "on" : ""}>
            <td>{r.cutoff}{r.cutoff === m.cutoff_time_utc ? " (selected)" : ""}</td>
            <td>{r.mean_horizon_h != null ? `${r.mean_horizon_h.toFixed(0)} h` : "–"}</td>
            <td>{fmtMW(r.mae)}</td><td>{fmtMW(r.rmse)}</td><td>{fmtMW(r.bias)}</td><td>{fmtMW(r.p90_abs)}</td></tr>)}</tbody>
        </table></div>
      </Card>}
    <Card title="Forecast vs actual (decision-time forecast)"><ResponsiveContainer width="100%" height={300}>
      <LineChart data={rows}><CartesianGrid stroke="#1f3a34" /><XAxis dataKey="startTime" tickFormatter={fmtTime} minTickGap={70} stroke="#8fa9a1" />
        <YAxis stroke="#8fa9a1" tickFormatter={axisMW} width={70} />
        <Tooltip contentStyle={tipStyle} labelFormatter={(l) => `${fmtTime(String(l))} UTC`} formatter={(v) => fmtMW(v)} /><Legend />
        <Line dataKey="forecast" name="Forecast (decision-time)" stroke="#3ddc97" dot={false} />
        <Line dataKey="actual" name="Actual" stroke="#4cc9f0" dot={false} /></LineChart></ResponsiveContainer></Card>
    <div className="grid2">
      <Card title="Error distribution" hint="Forecast − actual per hourly slot. Positive = wind over-forecast (shortfall risk)."><ResponsiveContainer width="100%" height={260}>
        <BarChart data={hist}><CartesianGrid stroke="#1f3a34" /><XAxis dataKey="bin" stroke="#8fa9a1" tickFormatter={axisMW} /><YAxis stroke="#8fa9a1" allowDecimals={false} />
          <Tooltip contentStyle={tipStyle} labelFormatter={(l) => `Error ≈ ${fmtMW(l)}`} formatter={(v) => [`${v} slots`, "Count"]} />
          <Bar dataKey="count" name="Slots" fill="#3ddc97" /></BarChart></ResponsiveContainer></Card>
      <Card title="By forecast horizon" hint="Target time minus publishTime, 6h bins."><Bars data={hz} x="horizon" /></Card>
      <Card title="By hour of day (UTC)"><Bars data={m.by_hour} x="hour" tick={hourTick} /></Card>
      <Card title="By delivery day"><Bars data={m.by_day} x="day" tick={(d) => fmtDay(String(d))} /></Card>
    </div>
  </>;
}
