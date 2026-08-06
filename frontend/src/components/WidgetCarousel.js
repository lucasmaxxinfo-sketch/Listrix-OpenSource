import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Package, Sparkles, TrendingUp, ImageIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { logClientEvent } from "@/lib/api";
import { formatMoney } from "@/lib/derive";

/* Auto-rotating widget system (Item / AI Insight / Market Summary). */
export const WidgetCarousel = ({ items = [], suggestions = [], perfIntel }) => {
  const navigate = useNavigate();
  const widgets = [];

  // Item widget
  const it = items[0];
  if (it) widgets.push({ key: "item", node: (
    <div className="flex items-center gap-4">
      {it.image ? <img src={it.image} alt={it.name} className="h-16 w-16 rounded-lg border border-border object-cover" /> : <span className="flex h-16 w-16 items-center justify-center rounded-lg bg-muted/40 text-muted-foreground"><ImageIcon size={22} /></span>}
      <div className="min-w-0">
        <p className="text-[11px] uppercase tracking-wide text-primary">Item Spotlight</p>
        <p className="truncate text-base font-semibold">{it.name}</p>
        <p className="text-sm text-muted-foreground">{it.condition} · {formatMoney(it.value_estimate?.mid ?? it.cost)}</p>
      </div>
    </div>
  ) });

  // AI insight widget
  const s = suggestions[0];
  if (s) widgets.push({ key: "insight", node: (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-[hsl(var(--lx-purple))]">AI Recommendation</p>
      <p className="mt-0.5 text-base font-semibold">{s.title}</p>
      <p className="text-sm text-muted-foreground line-clamp-1">{s.item_name} · {Math.round(s.confidence)}% confidence</p>
    </div>
  ) });

  // Market summary widget
  if (perfIntel) widgets.push({ key: "market", node: (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-[hsl(var(--lx-green))]">Market Summary</p>
      <p className="mt-0.5 text-base font-semibold">{formatMoney(perfIntel.predicted_revenue_opportunity)} revenue opportunity</p>
      <p className="text-sm text-muted-foreground">{perfIntel.best_performing?.length || 0} strong · {perfIntel.worst_performing?.length || 0} struggling · {perfIntel.summary?.pending_actions || 0} actions</p>
    </div>
  ) });

  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (widgets.length <= 1) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % widgets.length), 8000);
    return () => clearInterval(t);
  }, [widgets.length]);
  useEffect(() => { logClientEvent({ type: "WIDGET_VIEWED", message: "Dashboard widget viewed" }); }, []);

  if (widgets.length === 0) return null;
  const active = widgets[idx % widgets.length];

  return (
    <div data-testid="widget-carousel" className="rounded-xl border border-border bg-card/50 p-4 shadow-panelSoft">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground"><TrendingUp size={14} /> Live Widgets</div>
        <div className="flex items-center gap-1">
          <button onClick={() => setIdx((i) => (i - 1 + widgets.length) % widgets.length)} className="rounded p-1 text-muted-foreground hover:text-foreground"><ChevronLeft size={16} /></button>
          <div className="flex gap-1">{widgets.map((w, i) => <span key={w.key} className={`h-1.5 w-1.5 rounded-full ${i === idx % widgets.length ? "bg-primary" : "bg-muted"}`} />)}</div>
          <button onClick={() => setIdx((i) => (i + 1) % widgets.length)} className="rounded p-1 text-muted-foreground hover:text-foreground"><ChevronRight size={16} /></button>
        </div>
      </div>
      <div className="mt-3 min-h-[76px]">{active.node}</div>
    </div>
  );
};

export default WidgetCarousel;
