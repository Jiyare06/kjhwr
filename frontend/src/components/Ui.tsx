import { ReactNode } from "react";
export const Loading = () => <div className="state"><div className="spinner" />Loading Elexon data… the first load of January 2026 can take a minute; later loads use the cache.</div>;
export const ErrorBox = ({ msg }: { msg: string }) => <div className="state error">Could not load data: {msg}. Check the backend is running and retry.</div>;
export const Empty = () => <div className="state">No data for these settings. Widen the date range or horizon filter.</div>;
export const Kpi = ({ label, value, unit }: { label: string; value: number | null | undefined; unit?: string }) =>
  <div className="kpi"><small>{label}</small><b>{value == null ? "–" : value.toLocaleString(undefined, { maximumFractionDigits: 1 })}{unit && value != null ? ` ${unit}` : ""}</b></div>;
export const Card = ({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) =>
  <section className="card"><h3>{title}</h3>{hint && <p className="hint">{hint}</p>}{children}</section>;
