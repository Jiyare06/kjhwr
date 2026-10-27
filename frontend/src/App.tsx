import { useEffect, useState } from "react";
import { fetchDecision, fetchMetrics, Metrics, Params, Row } from "./api";
import { AccuracyView } from "./components/AccuracyView";
import { ForecastView } from "./components/ForecastView";
import { ErrorBox, Loading } from "./components/Ui";

function toCsv(rows: Row[]) {
  const cols: (keyof Row)[] = ["delivery_day", "startTime", "publishTime", "horizon_h", "forecast", "actual", "error"];
  return [cols.join(","), ...rows.map(r => cols.map(c => r[c] ?? "").join(","))].join("\n");
}

export default function App() {
  const [tab, setTab] = useState<"forecast" | "accuracy">("forecast");
  const [day, setDay] = useState("2026-01-15");
  const [p, setP] = useState<Params>({ start: "2026-01-01", end: "2026-01-31", cutoff: "09:00" });
  const [bp, setBp] = useState(90);
  const [dec, setDec] = useState<{ stats: Record<string, number | null>; rows: Row[] } | null>(null);
  const [all, setAll] = useState<{ rows: Row[]; m: Metrics } | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [err, setErr] = useState("");

  useEffect(() => {
    setState("loading");
    const one = { ...p, start: day, end: day };
    Promise.all([fetchDecision(one), fetchDecision(p), fetchMetrics(p, bp)])
      .then(([d, a, m]) => { setDec(d); setAll({ rows: a.rows, m }); setState("idle"); })
      .catch(e => { setErr(String(e.message ?? e)); setState("error"); });
  }, [day, p, bp]);

  const set = (k: keyof Params) => (e: { target: { value: string } }) => setP({ ...p, [k]: e.target.value });
  const download = () => {
    const url = URL.createObjectURL(new Blob([toCsv(all?.rows ?? [])], { type: "text/csv" }));
    Object.assign(document.createElement("a"), { href: url, download: "wind_decision_table.csv" }).click();
  };

  return <div className="wrap">
    <header><div className="brand">Wind<span>Monitor</span></div><button className="ghost" onClick={download} disabled={!all}>Export CSV</button></header>
    <h1>Day-ahead wind forecast monitor</h1>
    <p className="sub">GB national wind, January 2026. See the forecast you would have had at your D-1 cutoff, and how wrong that forecast has been. All times UTC.</p>
    <section className="card"><div className="controls">
      <label>Delivery day<input type="date" min="2026-01-01" max="2026-01-31" value={day} onChange={e => setDay(e.target.value)} /></label>
      <label>Decision cutoff (D-1, UTC)<input type="time" value={p.cutoff} onChange={set("cutoff")} /></label>
      <label>Accuracy from<input type="date" min="2026-01-01" max="2026-01-31" value={p.start} onChange={set("start")} /></label>
      <label>Accuracy to<input type="date" min="2026-01-01" max="2026-01-31" value={p.end} onChange={set("end")} /></label>
      <label>Min horizon (h)<input type="number" min={0} value={p.horizonMin ?? ""} onChange={set("horizonMin")} /></label>
      <label>Max horizon (h)<input type="number" min={0} value={p.horizonMax ?? ""} onChange={set("horizonMax")} /></label>
    </div></section>
    <div className="tabs"><button className={tab === "forecast" ? "on" : ""} onClick={() => setTab("forecast")}>Forecast for delivery day</button>
      <button className={tab === "accuracy" ? "on" : ""} onClick={() => setTab("accuracy")}>Accuracy & buffer</button></div>
    {state === "loading" && <Loading />}
    {state === "error" && <ErrorBox msg={err} />}
    {state === "idle" && tab === "forecast" && dec && <ForecastView rows={dec.rows} stats={dec.stats} />}
    {state === "idle" && tab === "accuracy" && all && <AccuracyView m={all.m} rows={all.rows} bp={bp} setBp={setBp} />}
  </div>;
}
