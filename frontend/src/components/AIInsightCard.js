import { TrendingUp, AlertTriangle, Gauge, ArrowRight } from "lucide-react";

const TONES = {
  green: { text: "text-[hsl(var(--lx-green))]", bar: "bg-[hsl(var(--lx-green))]", chip: "bg-[rgba(34,197,94,0.12)] border-[rgba(34,197,94,0.3)]", icon: TrendingUp },
  orange: { text: "text-primary", bar: "bg-primary", chip: "bg-[rgba(255,122,26,0.12)] border-primary/30", icon: Gauge },
  blue: { text: "text-[hsl(var(--lx-blue))]", bar: "bg-[hsl(var(--lx-blue))]", chip: "bg-[rgba(59,130,246,0.12)] border-[rgba(59,130,246,0.3)]", icon: AlertTriangle },
};

export const AIInsightCard = ({ insight, onAction }) => {
  const tone = TONES[insight.tone] || TONES.orange;
  const Icon = tone.icon;
  return (
    <div
      data-testid="ai-insight-card"
      className="rounded-xl border border-border bg-card/55 p-4 shadow-panelSoft"
    >
      <div className="flex items-center justify-between gap-2">
        <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold ${tone.chip} ${tone.text}`}>
          <Icon size={13} /> {insight.label}
        </span>
        <span data-testid="ai-insight-confidence" className="font-mono text-[11px] text-muted-foreground">{insight.confidence}% conf.</span>
      </div>

      <h4 className="mt-2 text-sm font-semibold">{insight.title}</h4>
      <p className="mt-1 text-sm text-foreground/80">{insight.summary}</p>

      <div className="mt-3">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/40">
          <div className={`h-full rounded-full ${tone.bar}`} style={{ width: `${insight.confidence}%` }} />
        </div>
      </div>

      {insight.action && (
        <button
          data-testid="ai-insight-primary-action-button"
          onClick={() => onAction?.(insight)}
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-1.5 text-xs font-semibold text-secondary-foreground transition-colors hover:bg-muted/50"
        >
          {insight.action} <ArrowRight size={13} />
        </button>
      )}
    </div>
  );
};

export default AIInsightCard;
