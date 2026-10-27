import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Row } from "../api";
import { Card, Empty, Kpi } from "./Ui";

export const ts = (s: string) => s.slice(5, 16).replace("T", " ");
const tipStyle = { background: "#0e1c19", border: "1px solid #1f3a34", borderRadius: 8 };

export function ForecastView({ rows, stats }: { rows: Row[]; stats: Record<string, number | null> }) {
  if (!rows.length) return <Empty />;
  const used = rows.filter(r => r.publishTime);
  const pubs = used.map(r => r.publishTime!).sort();
  return <>
    <div className="kpis">
      <Kpi label="Mean forecast" value={stats.mean} unit="MW" /><Kpi label="Min" value={stats.min} unit="MW" />
      <Kpi label="Max" value={stats.max} unit="MW" /><Kpi label="Slots without forecast" value={stats.missing_slots} />
    </div>
    <Card title="Latest forecast available at the decision cutoff"
      hint={pubs.length ? `Forecast publishTime used: ${ts(pubs[0])} → ${ts(pubs[pubs.length - 1])} UTC. All times UTC.` : "No forecast was published before the cutoff."}>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={rows}><CartesianGrid stroke="#1f3a34" /><XAxis dataKey="startTime" tickFormatter={ts} minTickGap={50} stroke="#8fa9a1" />
          <YAxis stroke="#8fa9a1" unit=" MW" width={80} /><Tooltip contentStyle={tipStyle} labelFormatter={(l) => `${l} UTC`} /><Legend />
          <Line dataKey="forecast" name="Forecast (decision-time)" stroke="#3ddc97" dot={false} strokeWidth={2} />
          <Line dataKey="actual" name="Actual (FUELHH)" stroke="#4cc9f0" dot={false} strokeWidth={2} /></LineChart>
      </ResponsiveContainer>
    </Card>
  </>;
}
