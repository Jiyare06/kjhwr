import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Row } from "../api";
import { axisMW, fmtMW, fmtTime, tipStyle } from "../format";
import { Card, Empty, Kpi } from "./Ui";

export function ForecastView({ rows, stats }: { rows: Row[]; stats: Record<string, number | null> }) {
  const [showActual, setShowActual] = useState(true);
  if (!rows.length) return <Empty />;
  const used = rows.filter(r => r.publishTime);
  const pubs = used.map(r => r.publishTime!).sort();
  return <>
    <div className="kpis">
      <Kpi label="Mean forecast" value={stats.mean} unit="MW" /><Kpi label="Min" value={stats.min} unit="MW" />
      <Kpi label="Max" value={stats.max} unit="MW" /><Kpi label="Slots without forecast" value={stats.missing_slots} />
    </div>
    <Card title="Latest forecast available at the decision cutoff"
      hint={pubs.length ? `Forecast published ${fmtTime(pubs[0])}${pubs[0] !== pubs[pubs.length - 1] ? ` → ${fmtTime(pubs[pubs.length - 1])}` : ""} UTC is the latest available at your cutoff. All times UTC.` : "No forecast was published before the cutoff."}>
      <label className="toggle"><input type="checkbox" checked={showActual} onChange={e => setShowActual(e.target.checked)} />
        Show actuals (backtesting only, not available at decision time)</label>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={rows}><CartesianGrid stroke="#1f3a34" /><XAxis dataKey="startTime" tickFormatter={fmtTime} minTickGap={50} stroke="#8fa9a1" />
          <YAxis stroke="#8fa9a1" tickFormatter={axisMW} width={70} />
          <Tooltip contentStyle={tipStyle} labelFormatter={(l) => `${fmtTime(String(l))} UTC`} formatter={(v) => fmtMW(v)} /><Legend />
          <Line dataKey="forecast" name="Forecast (decision-time)" stroke="#3ddc97" dot={false} strokeWidth={2} />
          {showActual && <Line dataKey="actual" name="Actual (backtest only)" stroke="#4cc9f0" dot={false} strokeWidth={2} />}</LineChart>
      </ResponsiveContainer>
    </Card>
  </>;
}
