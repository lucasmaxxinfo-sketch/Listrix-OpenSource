import { PackagePlus, Sparkles, AlertTriangle, DollarSign, Lightbulb, Activity, Eye, TrendingUp, CheckCircle2, XCircle, ListChecks, ShieldCheck, Gauge } from "lucide-react";
import { formatTime } from "@/lib/derive";

const TYPE_META = {
  ITEM_CREATED: { color: "hsl(var(--lx-blue))", icon: PackagePlus, label: "Item Created" },
  LISTING_GENERATED: { color: "hsl(var(--lx-green))", icon: Sparkles, label: "Listing Generated" },
  PRICE_UPDATED: { color: "hsl(var(--lx-orange))", icon: DollarSign, label: "Price Updated" },
  INSIGHT: { color: "hsl(var(--lx-purple))", icon: Lightbulb, label: "Insight" },
  AI_ERROR: { color: "hsl(var(--destructive))", icon: AlertTriangle, label: "AI Error" },
  LISTING_PERFORMANCE_UPDATED: { color: "hsl(var(--lx-blue))", icon: Gauge, label: "Performance Updated" },
  AI_SUGGESTION_CREATED: { color: "hsl(var(--lx-purple))", icon: Lightbulb, label: "Suggestion Created" },
  AI_SUGGESTION_APPLIED: { color: "hsl(var(--lx-green))", icon: CheckCircle2, label: "Suggestion Applied" },
  IMAGE_ANALYSED: { color: "hsl(var(--lx-purple))", icon: Eye, label: "Image Analysed" },
  VALUE_ESTIMATED: { color: "hsl(var(--lx-orange))", icon: DollarSign, label: "Value Estimated" },
  MARKET_MATCH_FOUND: { color: "hsl(var(--lx-blue))", icon: TrendingUp, label: "Market Match" },
  MARKET_SIGNAL_UPDATED: { color: "hsl(var(--lx-blue))", icon: TrendingUp, label: "Market Signal" },
  LISTING_VIEW_ESTIMATED: { color: "hsl(var(--lx-purple))", icon: Eye, label: "Views Estimated" },
  ACTION_QUEUED: { color: "hsl(var(--lx-orange))", icon: ListChecks, label: "Action Queued" },
  ACTION_APPROVED: { color: "hsl(var(--lx-green))", icon: CheckCircle2, label: "Action Approved" },
  ACTION_REJECTED: { color: "hsl(var(--destructive))", icon: XCircle, label: "Action Rejected" },
  USER_APPROVED_ACTION: { color: "hsl(var(--lx-green))", icon: ShieldCheck, label: "User Approved" },
  VOICE_QUERY_RECEIVED: { color: "hsl(var(--lx-purple))", icon: Activity, label: "Voice Query" },
  WIDGET_VIEWED: { color: "hsl(var(--muted-foreground))", icon: Eye, label: "Widget Viewed" },
  AI_BRIEFING_GENERATED: { color: "hsl(var(--lx-orange))", icon: Lightbulb, label: "Briefing Generated" },
  PERFORMANCE_RECALCULATED: { color: "hsl(var(--lx-blue))", icon: Gauge, label: "Performance Recalculated" },
};

export const EventTimeline = ({ events = [], emptyText = "No activity yet." }) => {
  if (events.length === 0) {
    return (
      <div className="flex h-40 flex-col items-center justify-center text-muted-foreground">
        <Activity size={22} className="mb-2" /><p className="text-sm">{emptyText}</p>
      </div>
    );
  }
  return (
    <ul data-testid="event-timeline" className="relative px-4 py-2 lx-scroll">
      {events.map((ev) => {
        const meta = TYPE_META[ev.type] || { color: "hsl(var(--muted-foreground))", icon: Activity, label: ev.type };
        const Icon = meta.icon;
        return (
          <li key={ev.id} data-testid="event-timeline-row" className="relative pl-8 py-3">
            <span className="absolute left-[13px] top-0 bottom-0 w-px bg-border" />
            <span className="absolute left-[7px] top-4 h-3 w-3 rounded-full ring-4 ring-background" style={{ backgroundColor: meta.color, boxShadow: `0 0 8px ${meta.color}` }} />
            <div className="flex items-center gap-2 flex-wrap">
              <Icon size={14} style={{ color: meta.color }} />
              <span data-testid="event-timeline-type" className="text-xs font-semibold" style={{ color: meta.color }}>{meta.label}</span>
              <span data-testid="event-timeline-timestamp" className="text-[11px] text-muted-foreground">{formatTime(ev.created_at)}</span>
            </div>
            <p className="mt-0.5 text-sm text-foreground/90">{ev.message}</p>
          </li>
        );
      })}
    </ul>
  );
};

export default EventTimeline;
