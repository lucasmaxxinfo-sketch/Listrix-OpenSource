import { Loader2, Sunrise, AlertTriangle, Lightbulb, ListChecks, RefreshCw } from "lucide-react";

export const DailyBriefing = ({ brief, loading, onRefresh, refreshing }) => {
  return (
    <div data-testid="daily-briefing" className="rounded-xl border border-primary/20 bg-card/60 p-5 shadow-orangeGlow lx-noise">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[rgba(255,122,26,0.12)] text-primary"><Sunrise size={18} /></span>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-primary">Daily AI Briefing</p>
            <h2 className="text-lg font-bold">{brief?.headline || "Your daily overview"}</h2>
          </div>
        </div>
        <button data-testid="refresh-brief-button" onClick={onRefresh} disabled={refreshing} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-1.5 text-xs font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-60">
        {refreshing ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />} {brief ? "Refresh" : "Generate"}
      </button>
      </div>

      {loading ? (
        <div className="flex h-20 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={20} /></div>
      ) : !brief ? (
        <p className="mt-3 text-sm text-muted-foreground">No briefing yet. Click Generate to get today's overview.</p>
      ) : (
        <>
          <p className="mt-3 text-sm text-foreground/85">{brief.summary}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <MiniList icon={ListChecks} title="Priorities" tone="text-primary" items={brief.priority_items} />
            <MiniList icon={AlertTriangle} title="Risks" tone="text-[hsl(var(--destructive))]" items={brief.risk_alerts} />
            <MiniList icon={Lightbulb} title="Opportunities" tone="text-[hsl(var(--lx-green))]" items={brief.opportunities} />
          </div>
          {brief.suggested_actions?.length > 0 && (
            <div className="mt-3 rounded-lg border border-border bg-muted/20 p-3">
              <p className="mb-1 text-[11px] uppercase tracking-wide text-muted-foreground">Suggested actions</p>
              <ul className="list-disc space-y-0.5 pl-4 text-sm text-foreground/85">{brief.suggested_actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

function MiniList({ icon: Icon, title, tone, items = [] }) {
  return (
    <div className="rounded-lg border border-border bg-card/50 p-3">
      <div className={`mb-1 flex items-center gap-1.5 text-xs font-semibold ${tone}`}><Icon size={13} /> {title}</div>
      {items.length === 0 ? <p className="text-xs text-muted-foreground">None</p> : (
        <ul className="space-y-0.5 text-xs text-foreground/80">{items.slice(0, 4).map((x, i) => <li key={i} className="line-clamp-1">• {x}</li>)}</ul>
      )}
    </div>
  );
}

export default DailyBriefing;
