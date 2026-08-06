import { useNavigate } from "react-router-dom";
import { PackageOpen } from "lucide-react";
import { conditionScore, confidenceFor, estimatedValue, formatMoney } from "@/lib/derive";
import { imageSrc } from "@/lib/api";

const CONF = {
  low: "bg-muted/50 text-muted-foreground border border-border",
  medium: "bg-[rgba(255,122,26,0.12)] text-primary border border-primary/30",
  high: "bg-[rgba(34,197,94,0.12)] text-[hsl(var(--lx-green))] border border-[rgba(34,197,94,0.3)]",
};

export default function DashboardTable({ items, listingIndex }) {
  const navigate = useNavigate();
  const rows = items.slice(0, 8);

  return (
    <section data-testid="dashboard-table" className="rounded-xl border border-border bg-card/40">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wide">Inventory Snapshot</h2>
          <p className="text-xs text-muted-foreground">Recent items with AI confidence and estimated value</p>
        </div>
        <button onClick={() => navigate("/items")} className="text-xs font-semibold text-primary hover:text-primary/80">View all</button>
      </div>
      {rows.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-10 text-sm text-muted-foreground">
          <PackageOpen size={28} />
          <p>No items yet. Add your first item to see it here.</p>
        </div>
      ) : (
        <div className="overflow-x-auto lx-scroll">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-[11px] uppercase tracking-wide text-muted-foreground">
                <th className="px-5 py-2.5 font-semibold">Item</th>
                <th className="px-4 py-2.5 font-semibold">Condition</th>
                <th className="px-4 py-2.5 font-semibold">Est. Value</th>
                <th className="px-4 py-2.5 font-semibold">AI Confidence</th>
                <th className="px-4 py-2.5 text-right font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => {
                const listing = listingIndex?.byItemId?.get(item.id) || listingIndex?.byName?.get(item.name) || null;
                const { level, pct } = confidenceFor(item, listing);
                const value = estimatedValue(item, listing);
                const score = conditionScore(item.condition);
                return (
                  <tr key={item.id} onClick={() => navigate(`/items/${item.id}`)} className="cursor-pointer border-b border-border/60 transition-colors last:border-0 hover:bg-muted/20" data-testid="dashboard-table-row">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 shrink-0 overflow-hidden rounded-lg bg-muted/30">
                          {imageSrc(item, true) ? <img src={imageSrc(item, true)} alt={item.name} className="h-full w-full object-cover" /> : <div className="flex h-full w-full items-center justify-center text-muted-foreground"><PackageOpen size={16} /></div>}
                        </div>
                        <div>
                          <p className="max-w-[260px] truncate font-medium hover:text-primary">{item.name}</p>
                          <p className="text-xs text-muted-foreground">{item.sku || item.category || "No SKU"}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-xs font-medium">{item.condition}</p>
                      <div className="mt-1 h-1 w-16 overflow-hidden rounded-full bg-muted/40"><div className="h-full rounded-full bg-primary/80" style={{ width: `${score}%` }} /></div>
                    </td>
                    <td className="px-4 py-3 text-base font-semibold tabular-nums">{formatMoney(value)}</td>
                    <td className="px-4 py-3"><span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${CONF[level]}`}>{level} · {pct}%</span></td>
                    <td className="px-4 py-3 text-right">
                      {item.sold ? <span className="rounded bg-[rgba(34,197,94,0.16)] px-2 py-0.5 text-[11px] font-semibold text-[hsl(var(--lx-green))]">Sold · {formatMoney(item.sale_price)}</span> : listing ? <span className="rounded bg-[rgba(34,197,94,0.12)] px-2 py-0.5 text-[11px] font-semibold text-[hsl(var(--lx-green))]">Listed</span> : <span className="rounded bg-muted/50 px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">Draft</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
