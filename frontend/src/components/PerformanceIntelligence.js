import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, AlertTriangle, DollarSign, ListChecks, ArrowUpRight } from "lucide-react";
import { formatMoney } from "@/lib/derive";

const RISK = { low: "text-[hsl(var(--lx-green))]", medium: "text-primary", high: "text-[hsl(var(--destructive))]" };

export const PerformanceIntelligence = ({ intel }) => {
  const navigate = useNavigate();
  if (!intel) return null;
  return (
    <section data-testid="performance-intelligence" className="rounded-xl border border-border bg-card/40">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <h2 className="text-sm font-semibold tracking-wide">Business Performance Intelligence</h2>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-[rgba(34,197,94,0.12)] px-2 py-0.5 text-xs font-semibold text-[hsl(var(--lx-green))]"><DollarSign size={13} /> {formatMoney(intel.predicted_revenue_opportunity)} opportunity</span>
      </div>
      <div className="grid gap-4 p-4 md:grid-cols-3">
        <Col icon={TrendingUp} tone="text-[hsl(var(--lx-green))]" title="Best Performing" rows={intel.best_performing} render={(r) => `${r.name} · ${Math.round(r.likelihood)}%`} onClick={(r) => navigate(`/items/${r.item_id}`)} empty="Run analysis to populate" />
        <Col icon={TrendingDown} tone="text-[hsl(var(--destructive))]" title="Worst Performing" rows={intel.worst_performing} render={(r) => `${r.name} · ${Math.round(r.likelihood)}%`} onClick={(r) => navigate(`/items/${r.item_id}`)} empty="None struggling" />
        <Col icon={AlertTriangle} tone="text-primary" title="Needs Attention" rows={intel.needs_attention} render={(r) => r.name} onClick={(r) => navigate(`/items/${r.item_id}`)} empty="All clear" />
      </div>
      {intel.recommended_next_actions?.length > 0 && (
        <div className="border-t border-border p-4">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground"><ListChecks size={14} /> AI Recommended Next Actions (urgency ranked)</div>
          <div className="space-y-2">
            {intel.recommended_next_actions.map((a) => (
              <button key={a.id} onClick={() => navigate("/ai-manager")} className="flex w-full items-center justify-between gap-3 rounded-lg border border-border bg-card/60 px-3 py-2 text-left transition-colors hover:border-primary/30">
                <div className="min-w-0"><p className="truncate text-sm font-medium">{a.title}</p><p className="truncate text-xs text-muted-foreground">{a.item_name}</p></div>
                <div className="flex shrink-0 items-center gap-2"><span className={`text-[11px] font-bold uppercase ${RISK[a.risk_level] || RISK.low}`}>{a.risk_level}</span><span className="text-xs text-muted-foreground">{Math.round(a.confidence)}%</span><ArrowUpRight size={14} className="text-muted-foreground" /></div>
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

function Col({ icon: Icon, tone, title, rows = [], render, onClick, empty }) {
  return (
    <div className="rounded-lg border border-border bg-card/50 p-3">
      <div className={`mb-2 flex items-center gap-1.5 text-xs font-semibold ${tone}`}><Icon size={13} /> {title}</div>
      {rows.length === 0 ? <p className="text-xs text-muted-foreground">{empty}</p> : (
        <ul className="space-y-1">{rows.map((r, i) => <li key={i}><button onClick={() => onClick(r)} className="w-full truncate text-left text-sm text-foreground/85 hover:text-foreground">{render(r)}</button></li>)}</ul>
      )}
    </div>
  );
}

export default PerformanceIntelligence;
