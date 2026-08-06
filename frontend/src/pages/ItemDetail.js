import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Loader2, Eye, DollarSign, TrendingUp, Gauge, Sparkles, History, ImageIcon, ShieldCheck, Play, BadgeCheck, Undo2 } from "lucide-react";
import { getItem, getItemSuggestions, getPerformance, getPriceHistory, getCompetitors, analyzeItem, generateListing, applySuggestion, dismissSuggestion, imageSrc } from "@/lib/api";
import { useMarkItemSold, useMarkItemUnsold } from "@/lib/queries";
import { formatMoney, formatTime } from "@/lib/derive";
import ActionCard from "@/components/ActionCard";
import ControlActionDialog from "@/components/ControlActionDialog";

export default function ItemDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [perf, setPerf] = useState(null);
  const [history, setHistory] = useState([]);
  const [comp, setComp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [dialog, setDialog] = useState(null);
  const [markOpen, setMarkOpen] = useState(false);
  const [salePrice, setSalePrice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [it, sg, pf, ph, cp] = await Promise.all([
        getItem(id), getItemSuggestions(id), getPerformance(), getPriceHistory(id), getCompetitors(id).catch(() => null),
      ]);
      setItem(it); setSuggestions(sg.filter((s) => s.status === "pending"));
      setPerf(pf.find((p) => p.item_id === id) || null); setHistory(ph); setComp(cp);
    } catch { toast.error("Failed to load item"); } finally { setLoading(false); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  const runAnalyze = async () => { setBusy(true); try { await analyzeItem(id); toast.success("Analysis complete"); await load(); } catch { toast.error("Analysis failed"); } finally { setBusy(false); } };
  const gen = async () => { setBusy(true); try { await generateListing({ name: item.name, description: item.description, condition: item.condition, cost: item.cost ?? null, item_id: id }); toast.success("Listing generated"); await load(); } catch { toast.error("Generation failed"); } finally { setBusy(false); } };
  const confirmApply = async () => { setBusy(true); try { const r = await applySuggestion(dialog.id); toast.success(r.change || "Applied"); setDialog(null); await load(); } catch { toast.error("Apply failed"); } finally { setBusy(false); } };
  const reject = async (s) => { setBusy(true); try { await dismissSuggestion(s.id); toast.success("Rejected"); await load(); } catch { toast.error("Reject failed"); } finally { setBusy(false); } };
  const markSold = useMarkItemSold();
  const markUnsold = useMarkItemUnsold();
  const handleMarkSold = async () => {
    const price = parseFloat(salePrice);
    if (!Number.isFinite(price) || price < 0) { toast.error("Enter a valid sale price"); return; }
    setBusy(true);
    try { await markSold.mutateAsync({ id, d: { sale_price: price } }); toast.success("Sale recorded — financials updated"); setMarkOpen(false); setSalePrice(""); await load(); }
    catch { toast.error("Failed to record sale"); } finally { setBusy(false); }
  };
  const handleMarkUnsold = async () => {
    setBusy(true);
    try { await markUnsold.mutateAsync(id); toast.success("Sale reverted"); await load(); }
    catch { toast.error("Failed to revert sale"); } finally { setBusy(false); }
  };

  if (loading) return <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>;
  if (!item) return <div className="text-muted-foreground">Item not found.</div>;

  const vision = item.vision; const ve = item.value_estimate; const ms = item.market_signal;
  const STATUS = { good: "text-[hsl(var(--lx-green))]", average: "text-primary", poor: "text-[hsl(var(--destructive))]" };

  return (
    <div data-testid="item-detail-page" className="space-y-6">
      <button onClick={() => navigate("/items")} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft size={15} /> Back to Items</button>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        {/* Left: media + actions */}
        <div className="space-y-4">
          <div className="overflow-hidden rounded-xl border border-border bg-card/60">
            <div className="aspect-square bg-muted/30">
              {imageSrc(item) ? <img src={imageSrc(item)} alt={item.name} className="h-full w-full object-cover" /> : <div className="flex h-full w-full items-center justify-center text-muted-foreground"><ImageIcon size={40} /></div>}
            </div>
            <div className="p-4">
              <h1 className="text-lg font-bold">{item.name}</h1>
              <p className="mt-1 text-sm text-muted-foreground">{item.condition}{item.category ? ` · ${item.category}` : ""}{item.cost != null ? ` · cost ${formatMoney(item.cost)}` : ""}</p>
              <p className="mt-2 text-sm text-foreground/80">{item.description}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button data-testid="detail-analyze-button" onClick={runAnalyze} disabled={busy} className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">{busy ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />} Analyze</button>
            <button onClick={gen} disabled={busy} className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-60"><Sparkles size={14} /> Generate</button>
          </div>

          {item.sold ? (
            <div data-testid="item-sold-panel" className="rounded-xl border border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.08)] p-4">
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--lx-green))]"><BadgeCheck size={14} /> Sold</div>
              <p className="mt-1 text-2xl font-bold tabular-nums">{formatMoney(item.sale_price)}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{item.sold_at ? `Sold ${formatTime(item.sold_at)}` : "Sale recorded"}</p>
              <button data-testid="detail-mark-unsold-button" onClick={handleMarkUnsold} disabled={busy} className="mt-3 inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-60"><Undo2 size={14} /> Revert sale</button>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card/40 p-4">
              {markOpen ? (
                <>
                  <label htmlFor="sale-price-input" className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Sale price</label>
                  <input id="sale-price-input" data-testid="sale-price-input" type="number" min="0" step="0.01" value={salePrice} onChange={(e) => setSalePrice(e.target.value)} placeholder="0.00" className="mt-1 w-full rounded-lg border border-border bg-secondary px-3 py-2 text-sm tabular-nums outline-none focus:border-primary/60" autoFocus />
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <button data-testid="confirm-mark-sold" onClick={handleMarkSold} disabled={busy} className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60"><BadgeCheck size={14} /> Confirm sale</button>
                    <button onClick={() => { setMarkOpen(false); setSalePrice(""); }} disabled={busy} className="inline-flex items-center justify-center rounded-lg border border-border bg-secondary px-3 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-60">Cancel</button>
                  </div>
                </>
              ) : (
                <button data-testid="detail-mark-sold-button" onClick={() => setMarkOpen(true)} disabled={busy} className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.08)] px-3 py-2 text-sm font-semibold text-[hsl(var(--lx-green))] transition-colors hover:bg-[rgba(34,197,94,0.14)] disabled:opacity-60"><BadgeCheck size={14} /> Mark Sold</button>
              )}
            </div>
          )}
        </div>

        {/* Right: Item Insight Panel */}
        <div data-testid="item-insight-panel" className="space-y-4">
          {perf && (
            <Panel icon={Gauge} title="Performance">
              <div className="flex flex-wrap items-center gap-4">
                <span className={`text-sm font-bold uppercase ${STATUS[perf.status] || ""}`}>{perf.status}</span>
                <span className="text-sm text-muted-foreground">{Math.round(perf.likelihood_of_sale)}% likely to sell</span>
                <span className="text-xs text-muted-foreground">{perf.time_on_market_hours}h on market</span>
              </div>
              <p className="mt-2 text-sm text-foreground/85">{perf.reason}</p>
              {perf.recommended_action && <p className="mt-1 text-sm text-primary">Next: {perf.recommended_action}</p>}
            </Panel>
          )}

          <Panel icon={Eye} title="AI Visual Analysis">
            {vision ? (
              <div className="space-y-1 text-sm">
                <Kv k="Identified" v={vision.item_type} /><Kv k="Category" v={vision.category} /><Kv k="Brand" v={vision.brand || "—"} /><Kv k="Condition (AI)" v={vision.condition_guess} />
                {vision.features?.length > 0 && <div className="mt-2 flex flex-wrap gap-1.5">{vision.features.map((f, i) => <span key={i} className="rounded-full bg-muted/50 px-2 py-0.5 text-[11px] text-muted-foreground">{f}</span>)}</div>}
              </div>
            ) : <p className="text-sm text-muted-foreground">No visual analysis. Upload an image during creation to enable it.</p>}
          </Panel>

          <Panel icon={DollarSign} title="Value Estimate">
            {ve ? (
              <div>
                <div className="flex items-end gap-4">
                  <div><p className="text-[11px] uppercase text-muted-foreground">Low</p><p className="text-lg font-semibold tabular-nums">{formatMoney(ve.low)}</p></div>
                  <div><p className="text-[11px] uppercase text-primary">Mid</p><p className="text-2xl font-bold tabular-nums text-primary">{formatMoney(ve.mid)}</p></div>
                  <div><p className="text-[11px] uppercase text-muted-foreground">High</p><p className="text-lg font-semibold tabular-nums">{formatMoney(ve.high)}</p></div>
                  <div className="ml-auto flex items-center gap-1 text-xs text-muted-foreground"><ShieldCheck size={13} /> {Math.round(ve.confidence)}%</div>
                </div>
                {ve.reasoning && <p className="mt-2 text-sm text-foreground/80">{ve.reasoning}</p>}
              </div>
            ) : <p className="text-sm text-muted-foreground">No value estimate yet.</p>}
          </Panel>

          <Panel icon={TrendingUp} title="Market Positioning & Signals">
            <div className="flex flex-wrap gap-4 text-sm">
              {comp && <Kv k="Positioning" v={comp.positioning} />}
              {ms && <><Kv k="Demand" v={ms.demand} /><Kv k="Competition" v={ms.competition} /><Kv k="Saturation" v={`${ms.saturation_pct}%`} /><Kv k="Price trend" v={ms.price_trend} /></>}
              {!ms && !comp && <p className="text-sm text-muted-foreground">Run analysis to compute market signals.</p>}
            </div>
            {comp?.simulated && <p className="mt-2 text-[11px] text-muted-foreground">Note: external competitor data is simulated/architected — live scraping not enabled yet.</p>}
          </Panel>

          {suggestions.length > 0 && (
            <Panel icon={Sparkles} title="Suggested Improvements (needs approval)">
              <div className="grid gap-3 sm:grid-cols-2">{suggestions.map((s) => <ActionCard key={s.id} suggestion={s} onApprove={setDialog} onReject={reject} busy={busy} />)}</div>
            </Panel>
          )}

          {history.length > 0 && (
            <Panel icon={History} title="Price History">
              <ul className="space-y-1 text-sm">{history.map((h) => <li key={h.id} className="flex items-center justify-between"><span className="text-muted-foreground">{formatTime(h.created_at)}</span><span>{formatMoney(h.old_price)} → <b className="text-primary">{formatMoney(h.new_price)}</b></span></li>)}</ul>
            </Panel>
          )}
        </div>
      </div>
      <ControlActionDialog suggestion={dialog} onConfirm={confirmApply} onClose={() => setDialog(null)} busy={busy} />
    </div>
  );
}

function Panel({ icon: Icon, title, children }) {
  return (
    <section className="rounded-xl border border-border bg-card/50">
      <div className="flex items-center gap-2 border-b border-border px-4 py-2.5"><Icon size={14} className="text-primary" /><h3 className="text-sm font-semibold">{title}</h3></div>
      <div className="p-4">{children}</div>
    </section>
  );
}
function Kv({ k, v }) { return <div><span className="text-[11px] uppercase text-muted-foreground">{k}</span><p className="font-medium capitalize">{v}</p></div>; }
