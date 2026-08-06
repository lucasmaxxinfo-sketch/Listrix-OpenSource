import { AlertTriangle, X, Check, Eye, Zap, ShieldAlert } from "lucide-react";

const RISK = {
  low: "text-[hsl(var(--lx-green))]",
  medium: "text-primary",
  high: "text-[hsl(var(--destructive))]",
};

function previewFor(s) {
  const p = s.params || {};
  switch (s.type) {
    case "reduce_price": return p.new_price != null ? `New price will be set to $${p.new_price}` : "Price will be reduced";
    case "improve_title": return p.new_title ? `New title: "${p.new_title}"` : "Listing title will be improved";
    case "add_keywords": return p.add_hashtags ? `Add keywords: ${p.add_hashtags.map((h) => "#" + h).join(", ")}` : "Keywords will be added";
    case "add_urgency": return p.urgency_text ? `Append: "${p.urgency_text}"` : "Urgency messaging will be added";
    case "relist": return "Item will be relisted (time-on-market reset)";
    case "generate_listing": return "A new AI listing will be generated for this item";
    default: return s.detail;
  }
}

/* Control Layer: no action executes without explicit confirmation here. */
export const ControlActionDialog = ({ suggestion, onConfirm, onClose, busy }) => {
  if (!suggestion) return null;
  const s = suggestion;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={busy ? undefined : onClose} />
      <div data-testid="control-action-dialog" className="relative w-full max-w-lg rounded-xl border border-primary/25 bg-card p-6 shadow-orangeGlowStrong">
        <div className="mb-4 flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[rgba(255,122,26,0.12)] text-primary"><ShieldAlert size={18} /></span>
            <div>
              <h3 className="text-sm font-semibold">Approve Action</h3>
              <p className="text-xs text-muted-foreground">{s.item_name}</p>
            </div>
          </div>
          <button onClick={onClose} disabled={busy} className="text-muted-foreground hover:text-foreground"><X size={18} /></button>
        </div>

        <h4 className="text-base font-bold">{s.title}</h4>

        <div className="mt-4 space-y-3 text-sm">
          <Row icon={Eye} label="Preview" value={previewFor(s)} />
          <Row icon={AlertTriangle} label="Explanation" value={s.reason || s.detail} />
          <Row icon={Zap} label="Expected impact" value={s.expected_outcome || s.expected_impact} />
          <div className="flex items-center gap-4 pt-1">
            <span className="text-xs text-muted-foreground">Confidence <b className="text-foreground">{Math.round(s.confidence)}%</b></span>
            <span className={`text-xs ${RISK[s.risk_level] || RISK.low}`}>Risk: <b>{s.risk_level || "low"}</b></span>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} disabled={busy} className="rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-50">Cancel</button>
          <button data-testid="confirm-action-button" onClick={onConfirm} disabled={busy} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">
            <Check size={16} /> {busy ? "Applying..." : "Approve & Apply"}
          </button>
        </div>
      </div>
    </div>
  );
};

function Row({ icon: Icon, label, value }) {
  return (
    <div className="flex gap-2">
      <Icon size={15} className="mt-0.5 shrink-0 text-muted-foreground" />
      <div><p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p><p className="text-foreground/90">{value}</p></div>
    </div>
  );
}

export default ControlActionDialog;
