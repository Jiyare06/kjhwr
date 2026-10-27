import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Metrics, Row } from "../api";
import { Card, Empty, Kpi } from "./Ui";
import { ts } from "./ForecastView";

const tip = { background: "#0e1c19", border: "1px solid #1f3a34", borderRadius: 8 };
const Bars = ({ data, x }: { data: any[]; x: string }) =>
  <ResponsiveContainer width="100%" height={260}><BarChart data={data}><CartesianGrid stroke="#1f3a34" />
    <XAxis dataKey={x} stroke="#8fa9a1" /><YAxis stroke="#8fa9a1" /><Tooltip contentStyle={tip} /><Legend />
    <Bar dataKey="mae" name="MAE (MW)" fill="#3ddc97" /><Bar dataKey="rmse" name="RMSE (MW)" fill="#4cc9f0" /><Bar dataKey="bias" name="Bias (MW)" fill="#ffb454" /></BarChart></ResponsiveContainer>;

export function AccuracyView({ m, rows, bp, setBp }: { m: Metrics; rows: Row[]; bp: number; setBp: (n: number) => void }) {
  const s = m.summary;
  if (!s.n) return <Empty />;
  const hist = m.histogram.map(h => ({ bin: Math.round((h.from + h.to) / 2), count: h.count }));
  const hz = [...m.by_horizon].sort((a, b) => parseInt(a.horizon!) - parseInt(b.horizon!));
  return <>
    <div className="kpis">
      <Kpi label="MAE" value={s.mae} unit="MW" /><Kpi label="RMSE" value={s.rmse} unit="MW" /><Kpi label="Bias (forecast − actual)" value={s.bias} unit="MW" />
      <Kpi label="MAPE" value={s.mape} unit="%" /><Kpi label="Slots scored" value={s.n} />
      {["p50", "p90", "p95", "p99"].map(k => <Kpi key={k} label={`|Error| ${k.toUpperCase()}`} value={s.abs_error_pct?.[k]} unit="MW" />)}
    </div>
    <Card title="Buffer recommendation (indicative)" hint="Conservative wind = forecast − P-th percentile of historical over-forecast error (floored at 0).">
      <label style={{ maxWidth: 240 }}>Confidence percentile: P{bp}
        <input type="range" min={50} max={99} value={bp} onChange={e => setBp(+e.target.value)} /></label>
      <div className="kpis" style={{ marginTop: 12 }}>
        <Kpi label="Extra power to procure (buffer)" value={m.buffer.buffer_mw} unit="MW" />
        <Kpi label="Mean forecast wind" value={m.buffer.mean_forecast} unit="MW" />
        <Kpi label="Mean conservative wind" value={m.buffer.mean_conservative_wind} unit="MW" /></div>
      <div className="callout">Indicative only. Based on one month of errors; assumes January 2026 is representative. Not a guarantee of cover.</div>
    </Card>
    <Card title="Forecast vs actual (decision-time forecast)"><ResponsiveContainer width="100%" height={300}>
      <LineChart data={rows}><CartesianGrid stroke="#1f3a34" /><XAxis dataKey="startTime" tickFormatter={ts} minTickGap={70} stroke="#8fa9a1" />
        <YAxis stroke="#8fa9a1" /><Tooltip contentStyle={tip} /><Legend />
        <Line dataKey="forecast" stroke="#3ddc97" dot={false} /><Line dataKey="actual" stroke="#4cc9f0" dot={false} /></LineChart></ResponsiveContainer></Card>
    <div className="grid2">
      <Card title="Error distribution (MW)" hint="Positive = wind over-forecast (shortfall risk)."><ResponsiveContainer width="100%" height={260}>
        <BarChart data={hist}><CartesianGrid stroke="#1f3a34" /><XAxis dataKey="bin" stroke="#8fa9a1" /><YAxis stroke="#8fa9a1" /><Tooltip contentStyle={tip} />
          <Bar dataKey="count" fill="#3ddc97" /></BarChart></ResponsiveContainer></Card>
      <Card title="By forecast horizon" hint="Target time minus publishTime, 6h bins."><Bars data={hz} x="horizon" /></Card>
      <Card title="By hour of day (UTC)"><Bars data={m.by_hour} x="hour" /></Card>
      <Card title="By delivery day"><Bars data={m.by_day.map(d => ({ ...d, day: d.day!.slice(8) }))} x="day" /></Card>
    </div>
  </>;
}
