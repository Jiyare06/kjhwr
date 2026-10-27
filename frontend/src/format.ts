// Shared display formatting. All times are UTC (the API returns "...Z" timestamps).
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const pad = (n: number) => String(n).padStart(2, "0");

/** "2026-01-15T18:00:00Z" -> "15 Jan 18:00" (UTC, independent of the viewer's time zone). */
export const fmtTime = (iso: string) => {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
};
/** "2026-01-15" -> "15 Jan" */
export const fmtDay = (day: string) => fmtTime(`${day}T00:00:00Z`).split(" ").slice(0, 2).join(" ");
export const fmtMW = (v: unknown) =>
  typeof v === "number" ? `${v.toLocaleString(undefined, { maximumFractionDigits: 0 })} MW` : "–";
/** Compact axis ticks: 12000 -> "12k MW" */
export const axisMW = (v: number) => `${Math.abs(v) >= 1000 ? `${+(v / 1000).toFixed(1)}k` : v} MW`;
export const tipStyle = { background: "#0e1c19", border: "1px solid #1f3a34", borderRadius: 8 };
