import { DollarSign, Type, Tags, RotateCw, Zap, Sparkles, Check, X, ShieldCheck } from "lucide-react";

const TYPE_META = {
  reduce_price: { icon: DollarSign, label: "Reduce Price" },
  improve_title: { icon: Type, label: "Improve Title" },
  add_keywords: { icon: Tags, label: "Add Keywords" },
  relist: { icon: RotateCw, label: "Relist" },
  add_urgency: { icon: Zap, label: "Add Urgency" },
  generate_listing: { icon: Sparkles, label: "Generate Listing" },
};
const RISK = {
  low: "bg-[rgba(34,197,94,0.12)] text-[hsl(var(--lx-green))] border-[rgba(34,197,94,0.3)]",
  medium: "bg-[rgba(255,122,26,0.12)] text-primary border-primary/30",
  high: "bg-[rgba(239,68,68,0.14)] text-[hsl(var(--destructive))] border-[rgba(239,68,68,0.3)]",
};

export const ActionCard = ({ suggestion, onApprove, onReject, busy }) => {
  const s = suggestion;
  const meta = TYPE_META[s.type] || { icon: Sparkles, label: s.type };
  const Icon = meta.icon;
  return (
    <div data-testid="action-card" className="rounded-xl border border-border bg-card/60 p-4 shadow-panelSoft transition-colors hover:border-primary/25">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-2 py-0.5 text-xs font-semibold text-muted-foreground"><Icon size={13} /> {meta.label}</span>
        <span className={`rounded-md border px-2 py-0.5 text-[11px] font-bold uppercase ${RISK[s.risk_level] || RISK.low}`}>{s.risk_level || "low"} risk</span>
      </div>
      <h4 className="mt-2 text-sm font-semibold">{s.title}</h4>
      <p className="text-xs text-muted-foreground">{s.item_name}</p>
      <p className="mt-2 text-sm text-foreground/85">{s.detail}</p>
      {(s.expected_outcome || s.expected_impact) && (
        <p className="mt-2 text-xs text-primary">Expected: {s.expected_outcome || s.expected_impact}</p>
      )}
      <div className="mt-3">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/40"><div className="h-full rounded-full bg-primary" style={{ width: `${s.confidence}%` }} /></div>
        <p className="mt-1 text-[11px] text-muted-foreground">{Math.round(s.confidence)}% confidence</p>
      </div>
      <div className="mt-3 flex gap-2">
        <button data-testid="action-approve-button" onClick={() => onApprove(s)} disabled={busy} className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60"><ShieldCheck size={14} /> Review & Approve</button>
        <button data-testid="action-reject-button" onClick={() => onReject(s)} disabled={busy} className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-xs font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-60"><X size={14} /> Reject</button>
      </div>
    </div>
  );
};

export default ActionCard;
