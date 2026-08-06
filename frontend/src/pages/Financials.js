import { Loader2, Package, Tag, DollarSign, Receipt, TrendingUp, Percent, Calculator, CircleDollarSign, BadgeCheck } from "lucide-react";
import { useFinancials } from "@/lib/queries";
import StatCard from "@/components/StatCard";

const SYMBOLS = { USD: "$", NZD: "$", AUD: "$", CAD: "$", EUR: "\u20AC", GBP: "\u00A3", JPY: "\u00A5" };

function money(v, currency = "USD") {
  if (v == null) return "\u2014";
  const sym = SYMBOLS[currency] || `${currency} `;
  return sym + Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pct(v) {
  return v == null ? "\u2014" : `${Number(v).toFixed(1)}%`;
}

export default function Financials() {
  const { data: fin, isLoading } = useFinancials();

  if (isLoading) return <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>;
  if (!fin) return <div className="rounded-xl border border-border bg-card/40 p-10 text-center text-sm text-muted-foreground">No financial data available yet.</div>;

  const t = fin.totals || {};
  const currency = fin.currency || "USD";

  return (
    <div data-testid="financials-page" className="space-y-6">
      <div className="flex items-start gap-3 rounded-xl border border-[rgba(255,122,26,0.25)] bg-[rgba(255,122,26,0.07)] px-4 py-3">
        <Calculator size={16} className="mt-0.5 shrink-0 text-primary" />
        <p className="text-xs leading-relaxed text-muted-foreground">{fin.note}</p>
      </div>

      <div data-testid="financials-stats" className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Items" value={t.items ?? 0} icon={Package} />
        <StatCard label="Listed" value={t.listed ?? 0} icon={Tag} />
        <StatCard label="Sold" value={t.sold ?? 0} icon={BadgeCheck} />
        <StatCard label="Invested" value={money(t.invested, currency)} icon={DollarSign} />
        <StatCard label="Realized Revenue" value={money(t.realized_revenue, currency)} icon={TrendingUp} accent />
        <StatCard label="Realized Net" value={money(t.realized_net_profit, currency)} icon={CircleDollarSign} accent />
        <StatCard label="Potential Revenue" value={money(t.potential_revenue, currency)} icon={TrendingUp} />
        <StatCard label="Potential Net" value={money(t.potential_net_profit, currency)} icon={CircleDollarSign} />
        <StatCard label="Net Profit (realized + potential)" value={money(t.net_profit, currency)} icon={Receipt} />
        <StatCard label="Net Margin" value={pct(t.net_margin_pct)} icon={Percent} />
      </div>

      <section data-testid="financials-categories" className="rounded-xl border border-border bg-card/40">
        <div className="border-b border-border px-5 py-3">
          <h2 className="text-sm font-semibold tracking-wide">By Category</h2>
          <p className="text-xs text-muted-foreground">Fee rate {pct(fin.marketplace_fee_rate * 100)} \u00B7 tax rate {pct(fin.tax_rate * 100)}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-2.5 font-medium">Category</th>
                <th className="px-3 py-2.5 font-medium">Items</th>
                <th className="px-3 py-2.5 font-medium">Sold</th>
                <th className="px-3 py-2.5 font-medium">Invested</th>
                <th className="px-3 py-2.5 font-medium">Potential Revenue</th>
                <th className="px-3 py-2.5 font-medium">Gross Profit</th>
                <th className="px-3 py-2.5 font-medium">Net Profit</th>
              </tr>
            </thead>
            <tbody>
              {(fin.by_category || []).map((c) => (
                <tr key={c.category} className="border-t border-border/60 hover:bg-muted/30">
                  <td className="px-5 py-2.5 font-medium">{c.category}</td>
                  <td className="px-3 py-2.5 text-muted-foreground">{c.count}</td>
                  <td className="px-3 py-2.5 text-muted-foreground">{c.sold ?? 0}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(c.invested, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(c.potential_revenue, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(c.gross_profit, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums text-primary">{money(c.net_profit, currency)}</td>
                </tr>
              ))}
              {(fin.by_category || []).length === 0 && (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-muted-foreground">No categorized items yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section data-testid="financials-items" className="rounded-xl border border-border bg-card/40">
        <div className="border-b border-border px-5 py-3"><h2 className="text-sm font-semibold tracking-wide">Top Items by Net Profit</h2></div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-2.5 font-medium">Item</th>
                <th className="px-3 py-2.5 font-medium">Status</th>
                <th className="px-3 py-2.5 font-medium">Category</th>
                <th className="px-3 py-2.5 font-medium">Cost</th>
                <th className="px-3 py-2.5 font-medium">Price</th>
                <th className="px-3 py-2.5 font-medium">Fees</th>
                <th className="px-3 py-2.5 font-medium">Tax</th>
                <th className="px-3 py-2.5 font-medium">Net</th>
                <th className="px-3 py-2.5 font-medium">Margin</th>
              </tr>
            </thead>
            <tbody>
              {(fin.items || []).map((r) => (
                <tr key={r.item_id} className="border-t border-border/60 hover:bg-muted/30">
                  <td className="px-5 py-2.5">
                    <div className="font-medium">{r.name}</div>
                    <div className="text-[11px] text-muted-foreground">{r.sold ? "Sold" : r.listed ? "Listed" : "Unlisted \u00B7 value estimate"}</div>
                  </td>
                  <td className="px-3 py-2.5">
                    {r.status === "sold" ? <span className="rounded bg-[rgba(34,197,94,0.12)] px-2 py-0.5 text-[11px] font-semibold text-[hsl(var(--lx-green))]">Sold</span> : <span className="text-muted-foreground">{r.status === "listed" ? "Listed" : "Open"}</span>}
                  </td>
                  <td className="px-3 py-2.5 text-muted-foreground">{r.category || "\u2014"}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(r.cost, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(r.price, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(r.estimated_fees, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums">{money(r.estimated_tax, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums text-primary">{money(r.net_profit, currency)}</td>
                  <td className="px-3 py-2.5 tabular-nums text-muted-foreground">{pct(r.margin_pct)}</td>
                </tr>
              ))}
              {(fin.items || []).length === 0 && (
                <tr><td colSpan={9} className="px-5 py-8 text-center text-muted-foreground">Add items with cost or a price estimate to see financial projections.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
