import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const ORANGE = "#f97316";
const GRID = "#2a2e37";
const TICK = "#9fa6b3";

function shortDay(day) {
  try {
    return new Date(`${day}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return day;
  }
}

function deriveByDay(events = []) {
  const counts = new Map();
  for (const e of events) {
    const d = (e.created_at || "").slice(0, 10);
    if (d) counts.set(d, (counts.get(d) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([day, count]) => ({ day, count }));
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-panelSoft">
      <p className="font-semibold">{label}</p>
      <p className="mt-0.5 text-muted-foreground">
        <span className="font-semibold tabular-nums text-[hsl(var(--lx-orange))]">{payload[0].value}</span> event{payload[0].value === 1 ? "" : "s"}
      </p>
    </div>
  );
}

export default function DashboardChart({ analytics, events }) {
  const source = analytics?.events_by_day?.length ? analytics.events_by_day : deriveByDay(events);
  const data = source.map((p) => ({ count: p.count || 0, day: shortDay(p.day), full: p.day }));
  const total = source.reduce((sum, p) => sum + (p.count || 0), 0);

  return (
    <section data-testid="dashboard-chart" className="rounded-xl border border-border bg-card/40">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wide">Activity Overview</h2>
          <p className="text-xs text-muted-foreground">Last {analytics?.days ?? 30} days · {total} events</p>
        </div>
        <span className="hidden rounded-full border border-primary/30 bg-[rgba(255,122,26,0.12)] px-2.5 py-1 text-[11px] font-semibold text-primary sm:inline-flex">Live</span>
      </div>
      {data.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">No activity to chart yet.</div>
      ) : (
        <div className="h-72 w-full p-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
              <defs>
                <linearGradient id="lxActivityFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={ORANGE} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={ORANGE} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="day" tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={{ stroke: GRID }} minTickGap={24} />
              <YAxis tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: ORANGE, strokeOpacity: 0.35, strokeDasharray: "4 4" }} />
              <Area type="monotone" dataKey="count" stroke={ORANGE} strokeWidth={2} fill="url(#lxActivityFill)" activeDot={{ r: 4, fill: ORANGE, stroke: "#0d0f13" }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
